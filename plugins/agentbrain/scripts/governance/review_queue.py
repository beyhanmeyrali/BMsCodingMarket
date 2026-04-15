"""
Memory Review Queue for AgentBrain

Shows memories awaiting promotion to wider scopes.
Implements the promotion workflow: user → team → project → org.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
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
    """Retrieve all memories from Qdrant."""
    try:
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
                "content": r.payload.get("content", ""),
                "created_at": parse_timestamp(r.payload.get("created_at")),
                "access_count": r.payload.get("access_count", 0),
                "thumbs_up": r.payload.get("thumbs_up", 0),
            }
            for r in all_points
        ]

    except Exception as e:
        print(f"Error retrieving memories: {e}", file=sys.stderr)
        return []


def get_promotion_candidates(memories: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Identify memories that are candidates for promotion.

    Promotion criteria:
    - High access count (≥ 3)
    - Positive feedback (thumbs_up > thumbs_down)
    - User scope only (not yet promoted)
    - Recent activity (created within last 90 days)

    Args:
        memories: List of memory dictionaries

    Returns:
        Dict with promotion candidates by current scope.
    """
    now = int(time.time())
    candidates = defaultdict(list)

    for memory in memories:
        scope = memory.get("scope", "")

        # Only consider user-scope memories for promotion
        if not scope.startswith("user:"):
            continue

        # Check access count
        access_count = memory.get("access_count", 0)
        if access_count < 3:
            continue

        # Check feedback
        thumbs_up = memory.get("thumbs_up", 0)
        thumbs_down = memory.get("thumbs_down", 0)
        if thumbs_down > thumbs_up:
            continue  # Skip if negative feedback

        # Check age (not too old)
        created_at = memory.get("created_at", 0)
        days_old = (now - created_at) // 86400 if created_at else 0
        if days_old > 90:
            continue  # Too old to consider

        # Calculate promotion score
        score = access_count + (thumbs_up * 2) - thumbs_down
        memory["promotion_score"] = score

        candidates["user"].append(memory)

    # Sort by score
    for scope in candidates:
        candidates[scope].sort(key=lambda m: m["promotion_score"], reverse=True)

    return dict(candidates)


def suggest_promotions(candidates: Dict[str, List[Dict]],
                      available_team: Optional[str] = None,
                      available_project: Optional[str] = None) -> List[Dict]:
    """
    Suggest specific promotions with target scopes.

    Args:
        candidates: Candidates by current scope
        available_team: Team name if available
        available_project: Project name if available

    Returns:
        List of promotion suggestions.
    """
    suggestions = []

    # User → Team promotions
    user_candidates = candidates.get("user", [])

    for memory in user_candidates[:10]:  # Top 10
        target_scopes = []

        if available_team:
            target_scopes.append(f"team:{available_team}")

        if available_project:
            target_scopes.append(f"project:{available_project}")

        if target_scopes:
            suggestions.append({
                "memory": memory,
                "from_scope": memory["scope"],
                "to_scopes": target_scopes,
                "reason": f"Accessed {memory.get('access_count', 0)} times, "
                         f"{memory.get('thumbs_up', 0)} thumbs up",
                "score": memory.get("promotion_score", 0),
            })

    return suggestions


def print_review_queue(candidates: Dict[str, List[Dict]],
                      suggestions: List[Dict]) -> None:
    """Print the review queue."""
    print("\n" + "=" * 60)
    print("AGENTBRAIN PROMOTION REVIEW QUEUE")
    print("=" * 60)

    total_candidates = sum(len(v) for v in candidates.values())

    if total_candidates == 0:
        print("\nNo memories awaiting promotion.")
        print("\nTo make memories eligible for promotion:")
        print("  - Use them frequently (access count increases)")
        print("  - Give positive feedback (thumbs up)")
        return

    print(f"\nTotal candidates: {total_candidates}")

    print("\n--- By Current Scope ---")
    for scope, mems in candidates.items():
        print(f"  {scope}: {len(mems)}")

    if suggestions:
        print("\n--- TOP PROMOTION SUGGESTIONS ---")
        for i, sugg in enumerate(suggestions[:5], 1):
            memory = sugg["memory"]
            print(f"\n{i}. {memory['file_path']}")
            print(f"   From: {sugg['from_scope']} → To: {', '.join(sugg['to_scopes'])}")
            print(f"   Reason: {sugg['reason']}")
            print(f"   Score: {sugg['score']}")
            if memory.get("content"):
                preview = memory["content"][:100].replace("\n", " ")
                print(f"   Preview: {preview}...")


def promote_memory(qdrant: QdrantProvider,
                   memory_id: str,
                   new_scope: str) -> bool:
    """
    Promote a memory to a wider scope.

    Args:
        qdrant: Qdrant provider
        memory_id: Memory ID to promote
        new_scope: New scope (e.g., "team:platform")

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Get the memory
        result = qdrant.client.retrieve(
            collection_name=qdrant.collection,
            ids=[memory_id],
            with_payload=True,
        )

        if not result:
            return False

        point = result[0]
        payload = dict(point.payload)
        payload["scope"] = new_scope
        payload["updated_at"] = int(time.time())

        # Update the point
        from qdrant_client.models import PointStruct
        qdrant.client.overwrite_payload(
            collection_name=qdrant.collection,
            payload=payload,
            points=[memory_id],
        )

        return True

    except Exception as e:
        print(f"Error promoting memory: {e}", file=sys.stderr)
        return False


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AgentBrain promotion review queue"
    )
    parser.add_argument(
        "--promote",
        type=str,
        help="Memory ID to promote"
    )
    parser.add_argument(
        "--to",
        type=str,
        help="Target scope (e.g., team:platform)"
    )
    parser.add_argument(
        "--team",
        type=str,
        help="Available team name for suggestions"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Available project name for suggestions"
    )
    parser.add_argument(
        "--auto",
        type=int,
        help="Auto-promote top N memories"
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

    candidates = get_promotion_candidates(memories)
    suggestions = suggest_promotions(
        candidates,
        available_team=args.team,
        available_project=args.project,
    )

    # Handle promotion
    if args.promote:
        if not args.to:
            print("Error: --to is required when using --promote", file=sys.stderr)
            return 1

        success = promote_memory(qdrant, args.promote, args.to)
        if success:
            print(f"Promoted {args.promote} to {args.to}")
        else:
            print(f"Failed to promote {args.promote}")
            return 1

    # Handle auto-promote
    elif args.auto:
        promoted = 0
        for sugg in suggestions[:args.auto]:
            memory_id = sugg["memory"]["id"]
            # Use first target scope
            target = sugg["to_scopes"][0]
            if promote_memory(qdrant, memory_id, target):
                print(f"Promoted: {sugg['memory']['file_path']} → {target}")
                promoted += 1

        print(f"\nPromoted {promoted} memories.")

    # Default: show queue
    else:
        print_review_queue(candidates, suggestions)

    return 0


if __name__ == "__main__":
    sys.exit(main())
