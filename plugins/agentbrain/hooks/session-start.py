"""
AgentBrain SessionStart Hook

Regenerates memory index, syncs repo memories, queries for relevant memories,
and injects them into the Claude Code context.

This hook runs automatically at the start of each session.
"""

import os
import sys
from pathlib import Path

# Add plugin scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from regenerate_index import generate_index, write_index
from query import query_memories, get_allowed_scopes, format_results


def sync_repo_memories() -> int:
    """
    Sync repository-based team memories to Qdrant.

    Returns:
        Number of memories synced.
    """
    try:
        from team_config import get_repo_memory_files
        from upsert import upsert_memory

        repo_files = get_repo_memory_files()
        count = 0

        for file_path in repo_files:
            try:
                upsert_memory(str(file_path))
                count += 1
            except Exception:
                pass  # Skip files that fail to upsert

        if count > 0:
            print(f"[AgentBrain] Synced {count} repo memories", file=sys.stderr)

        return count

    except Exception:
        return 0


def get_context_query() -> str:
    """
    Generate a context query based on current session state.

    Returns:
        Query string for semantic search.
    """
    # For now, use a generic query
    # In Phase 1, we'll analyze recent prompts/session context
    return "current context preferences decisions workflow conventions"


def inject_into_context(memories_content: str) -> None:
    """
    Inject retrieved memories into the session context.

    This outputs to stdout which gets captured by Claude Code.

    Args:
        memories_content: Formatted memories to inject.
    """
    if not memories_content or "No relevant memories found" in memories_content:
        return

    # Output with special marker for Claude Code to pick up
    print("\n" + "=" * 60)
    print("AGENTBRAIN CONTEXT INJECTION")
    print("=" * 60)
    print(memories_content)
    print("=" * 60 + "\n")


def main():
    """Main entry point for SessionStart hook."""

    # Skip if AgentBrain is explicitly disabled
    if os.environ.get("AGENTBRAIN_ENABLED", "true").lower() == "false":
        return

    # Step 1: Sync repo memories to Qdrant
    try:
        sync_repo_memories()
    except Exception as e:
        print(f"[AgentBrain] Warning: Failed to sync repo memories: {e}", file=sys.stderr)

    # Step 2: Regenerate MEMORY.md index (fast, ~50ms)
    try:
        index_content, count = generate_index()
        write_index(index_content)
    except Exception as e:
        # Non-fatal: log and continue
        print(f"[AgentBrain] Warning: Failed to regenerate index: {e}", file=sys.stderr)

    # Step 3: Get allowed scopes for this session
    try:
        scopes = get_allowed_scopes()
    except Exception as e:
        print(f"[AgentBrain] Warning: Failed to get scopes: {e}", file=sys.stderr)
        scopes = []

    # Step 4: Query for relevant memories
    try:
        query = get_context_query()
        results = query_memories(query=query, scopes=scopes, top_k=5)

        if results:
            memories_content = format_results(results)
            inject_into_context(memories_content)

    except Exception as e:
        # Non-fatal: log and continue
        print(f"[AgentBrain] Warning: Query failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
