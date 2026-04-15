"""
/recall skill implementation

Performs semantic search on stored memories and returns relevant results.
"""

import os
import sys
from pathlib import Path

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from query import query_memories, get_allowed_scopes, format_results


def skill_recall(query: str) -> str:
    """
    Search memories by semantic meaning.

    Args:
        query: Search query text

    Returns:
        Formatted results as markdown.
    """
    if not query or not query.strip():
        return "# Please provide a search query\n\nUsage: `/recall \"your query\"`"

    # Get allowed scopes
    scopes = get_allowed_scopes()

    # Query memories
    results = query_memories(
        query=query,
        scopes=scopes,
        top_k=8,
        min_score=0.5,
    )

    # Format results
    if not results:
        return f"# No relevant memories found\n\n> Query: \"{query}\"\n\nTry different keywords or use `/remember` to store this information."

    return format_results(results)


def main():
    """CLI entry point for testing."""
    if len(sys.argv) < 2:
        print("Usage: python skill_recall.py \"query\"")
        return 1

    query = " ".join(sys.argv[1:])
    result = skill_recall(query)
    print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
