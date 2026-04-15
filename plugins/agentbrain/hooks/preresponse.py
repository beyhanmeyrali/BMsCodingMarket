"""
AgentBrain PreResponse Hook

Automatically queries relevant memories before each Claude response.
Injects relevant context invisibly - user doesn't need to know.
"""

import os
import sys
from pathlib import Path

# Add plugin scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from query import query_memories, get_allowed_scopes, format_results


def should_query_context(user_message: str) -> bool:
    """
    Determine if the user message might benefit from memory lookup.

    Args:
        user_message: The user's input message

    Returns:
        True if memory lookup is worthwhile.
    """
    if not user_message or len(user_message) < 10:
        return False

    # Skip purely technical requests
    skip_patterns = [
        "/test",
        "/run",
        "/debug",
        "open file",
        "read file",
        "write file",
        "create file",
    ]

    user_lower = user_message.lower()
    for pattern in skip_patterns:
        if pattern in user_lower:
            return False

    # Questions that often relate to past decisions:
    question_indicators = [
        "how do i",
        "what do",
        "how to",
        "what's our",
        "what are",
        "remember",
        "convention",
        "prefer",
        "should i",
        "standard",
        "approach",
        "decision",
        "choice",
    ]

    return any(indicator in user_lower for indicator in question_indicators)


def inject_relevant_memories(user_message: str) -> str:
    """
    Query and format relevant memories for injection.

    Args:
        user_message: The user's message to use as query

    Returns:
        Formatted memories or empty string.
    """
    try:
        scopes = get_allowed_scopes()
        results = query_memories(
            query=user_message,
            scopes=scopes,
            top_k=3,
            min_score=0.6,
        )

        if not results:
            return ""

        return format_results(results)

    except Exception:
        return ""


def main():
    """
    PreResponse hook entry point.

    Reads user message from stdin, queries relevant memories,
    and injects them into context.
    """
    # Skip if AgentBrain is disabled
    if os.environ.get("AGENTBRAIN_ENABLED", "true").lower() == "false":
        return

    # Read user message from stdin (Claude Code provides this)
    user_message = sys.stdin.read().strip()

    if not user_message:
        return

    # Check if this message type benefits from memory lookup
    if not should_query_context(user_message):
        return

    # Query for relevant memories
    memories_content = inject_relevant_memories(user_message)

    if not memories_content or "No relevant memories found" in memories_content:
        return

    # Output with special marker for Claude Code
    print("\n" + "=" * 60)
    print("AGENTBRAIN CONTEXT")
    print("=" * 60)
    print(memories_content)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
