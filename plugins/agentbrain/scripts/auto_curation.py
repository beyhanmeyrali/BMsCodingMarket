"""
Auto-Curation Module

Automatically promotes memories based on usage patterns to prevent silos.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.qdrant import QdrantProvider


def get_config() -> dict:
    """Get auto-curation configuration."""
    return {
        "qdrant_host": os.environ.get("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.environ.get("QDRANT_PORT", "6333")),
        "qdrant_collection": os.environ.get("QDRANT_COLLECTION", "agentbrain_memories"),
        "embedding_dim": int(os.environ.get("EMBEDDING_DIMENSION", "1024")),
        "auto_promote_threshold": int(os.environ.get("AUTO_PROMOTE_THRESHOLD", "3")),
        "team_scope": os.environ.get("AGENTBRAIN_TEAM_ID", ""),
        "project_scope": os.environ.get("AGENTBRAIN_PROJECT_ID", ""),
    }


def track_memory_access(memory_id: str) -> bool:
    """
    Track that a memory was accessed.

    Args:
        memory_id: Memory ID to track

    Returns:
        True if successful.
    """
    try:
        config = get_config()
        qdrant = QdrantProvider(
            host=config["qdrant_host"],
            port=config["qdrant_port"],
            collection=config["qdrant_collection"],
            embedding_dim=config["auto_promote_threshold"],
        )
        qdrant.initialize()

        # Get current memory
        memory = qdrant.get_by_id(memory_id)
        if not memory:
            return False

        # Increment access count
        payload = memory.metadata.copy()
        payload["access_count"] = payload.get("access_count", 0) + 1
        payload["last_accessed"] = int(time.time())

        # Update
        from qdrant_client.models import PointStruct
        qdrant.client.overwrite_payload(
            collection_name=qdrant.collection,
            payload=payload,
            points=[memory_id],
        )

        # Check if should auto-promote
        access_count = payload["access_count"]
        threshold = config["auto_promote_threshold"]

        if access_count >= threshold and memory.scope.startswith("user:"):
            # Auto-promote to team or project
            target_scope = None
            if config["team_scope"]:
                target_scope = f"team:{config['team_scope']}"
            elif config["project_scope"]:
                target_scope = f"project:{config['project_scope']}"

            if target_scope:
                payload["scope"] = target_scope
                qdrant.client.overwrite_payload(
                    collection_name=qdrant.collection,
                    payload=payload,
                    points=[memory_id],
                )
                return True  # Promoted

        return True  # Tracked but not promoted

    except Exception as e:
        print(f"Error tracking access: {e}", file=sys.stderr)
        return False


def find_promotable_memories() -> List[Dict]:
    """
    Find memories that should be promoted based on usage.

    Returns:
        List of memories ready for promotion.
    """
    try:
        config = get_config()
        qdrant = QdrantProvider(
            host=config["qdrant_host"],
            port=config["qdrant_port"],
            collection=config["qdrant_collection"],
            embedding_dim=config["embedding_dim"],
        )
        qdrant.initialize()

        # Get all memories
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

        promotable = []
        threshold = config["auto_promote_threshold"]

        for r in all_points:
            payload = r.payload
            scope = payload.get("scope", "")
            access_count = payload.get("access_count", 0)

            # Only user-scoped memories
            if not scope.startswith("user:"):
                continue

            # High access count
            if access_count >= threshold:
                promotable.append({
                    "id": r.id,
                    "file_path": payload.get("file_path", ""),
                    "scope": scope,
                    "access_count": access_count,
                })

        return promotable

    except Exception as e:
        print(f"Error finding promotable: {e}", file=sys.stderr)
        return []


def auto_promote_memories() -> int:
    """
    Automatically promote frequently accessed memories.

    Returns:
        Number of memories promoted.
    """
    promotable = find_promotable_memories()
    config = get_config()

    if not promotable:
        return 0

    # Determine target scope
    target_scope = None
    if config["team_scope"]:
        target_scope = f"team:{config['team_scope']}"
    elif config["project_scope"]:
        target_scope = f"project:{config['project_scope']}"

    if not target_scope:
        return 0

    # Promote
    promoted = 0
    qdrant = QdrantProvider(
        host=config["qdrant_host"],
        port=config["qdrant_port"],
        collection=config["qdrant_collection"],
        embedding_dim=config["embedding_dim"],
    )
    qdrant.initialize()

    for memory in promotable:
        try:
            payload = {"scope": target_scope}
            qdrant.client.overwrite_payload(
                collection_name=qdrant.collection,
                payload=payload,
                points=[memory["id"]],
            )
            promoted += 1
            print(f"[AgentBrain] Auto-promoted: {memory['file_path']} ({memory['access_count']} accesses)",
                  file=sys.stderr)
        except Exception as e:
            print(f"Error promoting {memory['file_path']}: {e}", file=sys.stderr)

    return promoted
