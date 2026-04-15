"""
Memory Stats Dashboard for AgentBrain

Tracks memory health, hit rates, and usage metrics to prevent context rot.
Highlights stale or low-quality memories for cleanup.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.qdrant import QdrantProvider


def get_config() -> dict:
    """Get configuration from environment variables."""
    return {
        "qdrant_host": os.environ.get("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.environ.get("QDRANT_PORT", "6333")),
        "qdrant_collection": os.environ.get("QDRANT_COLLECTION", "agentbrain_memories"),
        "embedding_dim": int(os.environ.get("EMBEDDING_DIMENSION", "1024")),
    }


def get_all_memories(qdrant: QdrantProvider) -> List[Dict]:
    """
    Retrieve all memories from Qdrant.

    Args:
        qdrant: Qdrant provider instance

    Returns:
        List of memory dictionaries with metadata.
    """
    try:
        # Scroll through all points
        from qdrant_client.models import ScrollRequest

        all_points = []
        offset = None

        while True:
            records, offset = qdrant.client.scroll(
                collection_name=qdrant.collection,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            all_points.extend(records)

            if offset is None:
                break

        def parse_timestamp(ts) -> int:
            """Parse timestamp to int (handles both string and int)."""
            if ts is None:
                return 0
            if isinstance(ts, int):
                return ts
            if isinstance(ts, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts)
                    return int(dt.timestamp())
                except Exception:
                    pass
            return 0

        return [
            {
                "id": r.id,
                "scope": r.payload.get("scope", "unknown"),
                "type": r.payload.get("type", "unknown"),
                "file_path": r.payload.get("file_path", ""),
                "created_at": parse_timestamp(r.payload.get("created_at")),
                "updated_at": parse_timestamp(r.payload.get("updated_at")),
                "access_count": r.payload.get("access_count", 0),
                "thumbs_up": r.payload.get("thumbs_up", 0),
                "thumbs_down": r.payload.get("thumbs_down", 0),
                "pinned": r.payload.get("pinned", False),
                "source": r.payload.get("source", "manual"),
                "provenance_weight": r.payload.get("provenance_weight", 0.5),
            }
            for r in all_points
        ]

    except Exception as e:
        print(f"Error retrieving memories: {e}", file=sys.stderr)
        return []


def calculate_score(memory: Dict, days_since_created: int, days_since_access: int) -> float:
    """
    Calculate a health score for a memory (0-100).

    Lower scores indicate potential rot.
    """
    score = 100.0

    # Decay for age
    if days_since_created > 180:
        score -= 30  # 6 months old
    elif days_since_created > 90:
        score -= 15  # 3 months old
    elif days_since_created > 30:
        score -= 5

    # Decay for lack of access
    if days_since_access > 60:
        score -= 40  # Never accessed in 2 months
    elif days_since_access > 30:
        score -= 20
    elif days_since_access > 14:
        score -= 5

    # Boost for provenance
    provenance = memory.get("provenance_weight", 0.5)
    score += provenance * 20

    # Boost for pinned
    if memory.get("pinned"):
        score += 30

    # Penalty for negative feedback
    thumbs_down = memory.get("thumbs_down", 0)
    thumbs_up = memory.get("thumbs_up", 0)
    total_votes = thumbs_up + thumbs_down

    if total_votes > 0:
        # Negative ratio penalizes more
        if thumbs_down > thumbs_up:
            score -= 30 * (thumbs_down / total_votes)
        elif thumbs_up > thumbs_down:
            score += 10 * (thumbs_up / total_votes)

    # Boost for recent access
    if memory.get("access_count", 0) > 5:
        score += 10

    return max(0, min(100, score))


def analyze_memory_health(memories: List[Dict]) -> Dict:
    """
    Analyze memory health and identify rot.

    Args:
        memories: List of memory dictionaries

    Returns:
        Health analysis results.
    """
    now = int(time.time())

    # Group by scope and type
    by_scope = defaultdict(list)
    by_type = defaultdict(list)

    stale_memories = []
    rot_candidates = []
    high_quality = []

    for memory in memories:
        scope = memory.get("scope", "unknown")
        mtype = memory.get("type", "unknown")

        by_scope[scope].append(memory)
        by_type[mtype].append(memory)

        # Calculate age
        created_at = memory.get("created_at", 0)
        updated_at = memory.get("updated_at", created_at)
        days_since_created = (now - created_at) // 86400 if created_at else 0
        days_since_access = (now - updated_at) // 86400 if updated_at else 0

        # Calculate score
        score = calculate_score(memory, days_since_created, days_since_access)
        memory["health_score"] = score
        memory["days_old"] = days_since_created
        memory["days_since_access"] = days_since_access

        # Categorize
        if score < 40 and not memory.get("pinned"):
            rot_candidates.append(memory)
        elif score < 60 and not memory.get("pinned"):
            stale_memories.append(memory)
        elif score >= 80:
            high_quality.append(memory)

    # Sort by score (ascending)
    rot_candidates.sort(key=lambda m: m["health_score"])
    stale_memories.sort(key=lambda m: m["health_score"])

    return {
        "total": len(memories),
        "by_scope": {k: len(v) for k, v in by_scope.items()},
        "by_type": {k: len(v) for k, v in by_type.items()},
        "rot_candidates": rot_candidates,
        "stale_memories": stale_memories,
        "high_quality": high_quality,
    }


def print_dashboard(analysis: Dict) -> None:
    """Print the stats dashboard."""
    print("\n" + "=" * 60)
    print("AGENTBRAIN MEMORY HEALTH DASHBOARD")
    print("=" * 60)

    print(f"\nTotal Memories: {analysis['total']}")

    print("\n--- By Scope ---")
    for scope, count in sorted(analysis["by_scope"].items()):
        print(f"  {scope}: {count}")

    print("\n--- By Type ---")
    for mtype, count in sorted(analysis["by_type"].items()):
        print(f"  {mtype}: {count}")

    print("\n--- Health Status ---")
    print(f"  High Quality (80+): {len(analysis['high_quality'])}")
    print(f"  Stale (40-60):      {len(analysis['stale_memories'])}")
    print(f"  ROT RISK (<40):     {len(analysis['rot_candidates'])}")

    # Show rot candidates
    if analysis["rot_candidates"]:
        print("\n*** ROT CANDIDATES (recommended for deletion) ***")
        for m in analysis["rot_candidates"][:10]:
            print(f"\n  [{m['health_score']:.0f}/100] {m['file_path']}")
            print(f"    Scope: {m['scope']} | Type: {m['type']}")
            print(f"    Age: {m['days_old']} days | Last access: {m['days_since_access']} days ago")
            print(f"    Accesses: {m.get('access_count', 0)} | Thumbs down: {m.get('thumbs_down', 0)}")

    # Show stale memories
    if analysis["stale_memories"]:
        print("\n*** STALE MEMORIES (consider review) ***")
        for m in analysis["stale_memories"][:5]:
            print(f"\n  [{m['health_score']:.0f}/100] {m['file_path']}")
            print(f"    Scope: {m['scope']} | Not accessed: {m['days_since_access']} days")


def suggest_cleanup(analysis: Dict) -> List[str]:
    """
    Suggest cleanup actions based on health analysis.

    Args:
        analysis: Health analysis results

    Returns:
        List of action suggestions.
    """
    suggestions = []

    rot_count = len(analysis["rot_candidates"])
    stale_count = len(analysis["stale_memories"])
    total = analysis["total"]

    if rot_count > 0:
        suggestions.append(
            f"DELETE {rot_count} memories with health < 40 (context rot)"
        )

    if stale_count > total * 0.3:
        suggestions.append(
            f"REVIEW {stale_count} stale memories ({stale_count/total*100:.0f}% of total)"
        )

    # Check for scope imbalance
    by_scope = analysis["by_scope"]
    user_count = by_scope.get("user:default", 0) + sum(
        v for k, v in by_scope.items() if k.startswith("user:")
    )

    if user_count > total * 0.7:
        suggestions.append(
            f"PROMOTE or DELETE low-value user memories ({user_count} = {user_count/total*100:.0f}% of total)"
        )

    return suggestions


def cleanup_rot(qdrant: QdrantProvider, rot_memories: List[Dict], dry_run: bool = True) -> int:
    """
    Delete rot memories to prevent context rot.

    Args:
        qdrant: Qdrant provider
        rot_memories: List of memories to delete
        dry_run: If True, only report what would be deleted

    Returns:
        Number of memories deleted.
    """
    deleted = 0

    for memory in rot_memories:
        memory_id = memory.get("id")
        file_path = memory.get("file_path", "unknown")

        if dry_run:
            print(f"Would delete: {file_path} (score: {memory.get('health_score', 0):.0f})")
        else:
            try:
                qdrant.client.delete(
                    collection_name=qdrant.collection,
                    points_selector=[memory_id],
                )
                deleted += 1

                # Also delete the memory file if it exists
                memory_dir = Path(os.environ.get("MEMORY_DIR", "~/.claude/memory")).expanduser()
                memory_file = memory_dir / file_path
                if memory_file.exists():
                    memory_file.unlink()

            except Exception as e:
                print(f"Error deleting {file_path}: {e}", file=sys.stderr)

    if not dry_run and deleted > 0:
        print(f"\nDeleted {deleted} memories to combat context rot.")

    return deleted


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AgentBrain memory health dashboard"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete rot memories (health < 40)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=40.0,
        help="Health score threshold for rot (default: 40)"
    )
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Show cleanup suggestions"
    )

    args = parser.parse_args()

    # Initialize Qdrant
    config = get_config()
    qdrant = QdrantProvider(
        host=config["qdrant_host"],
        port=config["qdrant_port"],
        collection=config["qdrant_collection"],
        embedding_dim=config["embedding_dim"],
    )
    qdrant.initialize()

    # Get and analyze memories
    memories = get_all_memories(qdrant)

    if not memories:
        print("No memories found.")
        return 0

    analysis = analyze_memory_health(memories)

    # Print dashboard
    print_dashboard(analysis)

    # Print suggestions
    if args.suggest:
        suggestions = suggest_cleanup(analysis)
        if suggestions:
            print("\n--- SUGGESTED ACTIONS ---")
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")

    # Cleanup
    if args.cleanup or args.dry_run:
        rot_memories = [m for m in analysis["rot_candidates"]
                       if m["health_score"] < args.score_threshold]

        if rot_memories:
            print(f"\n--- CLEANUP {'(DRY RUN)' if args.dry_run else ''} ---")
            deleted = cleanup_rot(qdrant, rot_memories, dry_run=args.dry_run)
        else:
            print("\nNo rot memories to clean up.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
