"""
AgentBrain UserPromptSubmit Hook

Captures explicit storage requests mid-conversation.
Patterns: "add to AgentBrain", "remember that", "save to memory"
"""

import os
import sys
import re
from pathlib import Path

# Add plugin scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from skill_remember import skill_remember


# Patterns that indicate explicit storage request
STORAGE_PATTERNS = [
    r"add to agentbrain",
    r"add that to agentbrain",
    r"save to agentbrain",
    r"remember that",
    r"don't forget",
    r"keep in mind",
    r"note that",
]


def should_store_immediately(user_message: str) -> bool:
    """Check if user wants to store something immediately."""
    if not user_message:
        return False

    user_lower = user_message.lower()

    for pattern in STORAGE_PATTERNS:
        if re.search(pattern, user_lower):
            return True

    return False


def extract_content_to_store(user_message: str) -> str:
    """
    Extract the actual content to store from user message.

    Examples:
    - "Add to AgentBrain: we use Redis" → "we use Redis"
    - "Remember that we always use TypeScript" → "we always use TypeScript"
    """
    # Remove the storage pattern to get the actual content
    content = user_message

    for pattern in STORAGE_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Get everything after the pattern
            parts = re.split(pattern, content, flags=re.IGNORECASE)
            if len(parts) > 1:
                content = parts[-1].strip()
                # Remove leading colon/dash if present
                content = re.sub(r"^[:\-\s]+", "", content)
                break

    return content.strip()


def main():
    """
    UserPromptSubmit hook entry point.

    Reads user prompt, checks if it's a storage request,
    and stores immediately.
    """
    # Skip if disabled
    if os.environ.get("AGENTBRAIN_IMMEDIATE_STORE", "true").lower() == "false":
        return

    # Read user message from stdin
    user_message = sys.stdin.read().strip()

    if not user_message:
        return

    # Check if this is a storage request
    if not should_store_immediately(user_message):
        return

    # Extract content to store
    content = extract_content_to_store(user_message)

    if not content or len(content) < 5:
        return

    # Store the memory
    try:
        result = skill_remember(content)

        # Log confirmation (visible to user)
        print(f"\n[AgentBrain] Stored to memory", file=sys.stderr)

    except Exception as e:
        print(f"[AgentBrain] Failed to store: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
