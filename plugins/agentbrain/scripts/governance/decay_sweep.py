"""
Memory Decay Sweep for AgentBrain

Automatically identifies and cleans up stale memories to prevent context rot.
Can be run as a scheduled task (cron) to maintain memory health.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.qdrant import QdrantProvider
from memory_stats import get_all_memories, analyze_memory_health


# Decay thresholds (configurable via environment)
DECAY_CONFIG = {
    "stale_days": int(os.environ.get("DECAY_STALE_DAYS", "60")),  # Days since access to consider stale
    "rot_days": int(os.environ.get("DECAY_ROT_DAYS", "90")),  # Days to consider as rot
    "min_access_count": int(os.environ.get("DECAY_MIN_ACCESS", "2")),  # Min accesses to protect from decay
    "protect_pinned": os.environ.get("DECAY_PROTECT_PINNED", "true").lower() == "true",
    "protect_adr": os.environ.get("DECAY_PROTECT_ADR", "true").lower() == "true",
    "auto_delete": os.environ.get("DECAY_AUTO_DELETE", "false").lower() == "true",
}


def find_stale_memories(memories: List[Dict], config: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Find stale and rot memories.

    Args:
        memories: List of memory dictionaries
        config: Decay configuration

    Returns:
        Tuple of (stale_memories, rot_memories)
    """
    now = int(time.time())
    stale = []
    rot = []

    for memory in memories:
        # Skip protected memories
        if config["protect_pinned"] and memory.get("pinned"):
            continue

        source = memory.get("source", "")
        if config["protect_adr"] and source == "adr":
            continue

        # Skip high-access memories
        if memory.get("access_count", 0) >= config["min_access_count"]:
            continue

        # Check last access time
        updated_at = memory.get("updated_at", memory.get("created_at", 0))
        days_since = (now - updated_at) // 86400 if updated_at else 999

        memory["days_stale"] = days_since

        if days_since >= config["rot_days"]:
            rot.append(memory)
        elif days_since >= config["stale_days"]:
            stale.append(memory)

    return stale, rot


def sweep(qdrant: QdrantProvider,
          config: Dict = None,
          dry_run: bool = False) -> Dict:
    """
    Run decay sweep on memories.

    Args:
        qdrant: Qdrant provider
        config: Decay configuration (uses DECAY_CONFIG if None)
        dry_run: If True, don't actually delete

    Returns:
        Sweep results.
    """
    if config is None:
        config = DECAY_CONFIG

    # Get all memories
    memories = get_all_memories(qdrant)

    if not memories:
        return {
            "total": 0,
            "stale": 0,
            "rot": 0,
            "deleted": 0,
        }

    # Analyze health
    analysis = analyze_memory_health(memories)

    # Find stale and rot
    stale, rot = find_stale_memories(memories, config)

    # Combine with health-based rot candidates
    health_rot = analysis.get("rot_candidates", [])
    all_rot = rot + [m for m in health_rot if m not in rot]

    results = {
        "total": len(memories),
        "stale": len(stale),
        "rot": len(all_rot),
        "deleted": 0,
        "stale_files": [m["file_path"] for m in stale[:10]],
        "rot_files": [m["file_path"] for m in all_rot[:10]],
    }

    # Delete rot if configured
    if config["auto_delete"] and not dry_run:
        for memory in all_rot:
            try:
                memory_id = memory.get("id")
                qdrant.client.delete(
                    collection_name=qdrant.collection,
                    points_selector=[memory_id],
                )
                results["deleted"] += 1
            except Exception as e:
                print(f"Error deleting {memory.get('file_path')}: {e}", file=sys.stderr)

    return results


def print_sweep_results(results: Dict, dry_run: bool = False) -> None:
    """Print sweep results."""
    mode = "DRY RUN" if dry_run else "SWEEP"

    print(f"\n{'='*60}")
    print(f"AGENTBRAIN DECAY SWEEP ({mode})")
    print(f"{'='*60}")

    print(f"\nTotal memories scanned: {results['total']}")
    print(f"Stale (≥{DECAY_CONFIG['stale_days']} days): {results['stale']}")
    print(f"Rot risk (≥{DECAY_CONFIG['rot_days']} days): {results['rot']}")

    if results.get("deleted"):
        print(f"\nDeleted: {results['deleted']} memories")

    if results["stale_files"]:
        print(f"\n--- Stale Memories (first 10) ---")
        for f in results["stale_files"]:
            print(f"  - {f}")

    if results["rot_files"]:
        print(f"\n--- Rot Memories (first 10) ---")
        for f in results["rot_files"]:
            print(f"  - {f}")

    # Action recommendation
    if results["rot"] > 0:
        print(f"\n*** RECOMMENDATION: Delete {results['rot']} rot memories ***")
        print("Set DECAY_AUTO_DELETE=true to auto-clean.")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AgentBrain memory decay sweep"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete rot memories"
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=DECAY_CONFIG["stale_days"],
        help=f"Days to consider stale (default: {DECAY_CONFIG['stale_days']})"
    )
    parser.add_argument(
        "--rot-days",
        type=int,
        default=DECAY_CONFIG["rot_days"],
        help=f"Days to consider rot (default: {DECAY_CONFIG['rot_days']})"
    )

    args = parser.parse_args()

    # Override config
    config = dict(DECAY_CONFIG)
    config["stale_days"] = args.stale_days
    config["rot_days"] = args.rot_days
    if args.delete:
        config["auto_delete"] = True

    # Initialize Qdrant
    from providers.qdrant import QdrantProvider

    qdrant = QdrantProvider(
        host=os.environ.get("QDRANT_HOST", "localhost"),
        port=int(os.environ.get("QDRANT_PORT", "6333")),
        collection=os.environ.get("QDRANT_COLLECTION", "agentbrain_memories"),
        embedding_dim=int(os.environ.get("EMBEDDING_DIMENSION", "1024")),
    )
    qdrant.initialize()

    # Run sweep
    results = sweep(qdrant, config, dry_run=not args.delete)

    # Print results
    print_sweep_results(results, dry_run=not args.delete)

    return 0


if __name__ == "__main__":
    sys.exit(main())
