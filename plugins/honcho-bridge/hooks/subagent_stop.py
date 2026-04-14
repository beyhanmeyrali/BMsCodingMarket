#!/usr/bin/env python3
"""
SubagentStop hook: Capture results from delegated subagent work.

Features:
- Capture subagent type and task
- Store learnings from parallel agents
- Track which subagents are used most frequently
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Fix Windows encoding issue
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from honcho import Honcho as HonchoClient
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False


def load_env_config():
    """Load configuration from .env file in current directory."""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env_config()


# Subagent type descriptions
SUBAGENT_DESCRIPTIONS = {
    "general-purpose": "General purpose exploration and research",
    "Explore": "Fast codebase exploration and pattern finding",
    "Plan": "Software architecture and implementation planning",
    "code-reviewer": "Code review against standards and plans",
    "statusline-setup": "Status line configuration",
}


def get_subagent_description(agent_type: str) -> str:
    """Get description for a subagent type."""
    return SUBAGENT_DESCRIPTIONS.get(agent_type, f"Agent type: {agent_type}")


def extract_learnings(result: dict) -> list:
    """
    Extract learnings from subagent result.

    Looks for:
    - Key findings
    - Discovered patterns
    - Decisions made
    - Problems solved
    """
    learnings = []

    if not result:
        return learnings

    # Try to parse result content
    content = ""
    if isinstance(result, dict):
        content = result.get("result", "") or result.get("output", "") or str(result)
    elif isinstance(result, str):
        content = result
    else:
        content = str(result)

    # Look for conclusion/summary patterns
    keywords = ["found:", "discovered:", "identified:", "detected:", "located:"]
    lines = content.split("\n")

    for line in lines:
        line_lower = line.strip().lower()
        if any(keyword in line_lower for keyword in keywords):
            learnings.append(line.strip())

    return learnings[:5]  # Limit to 5 key learnings


def store_subagent_result(
    agent_type: str,
    description: str,
    learnings: list,
    base_url: str,
    workspace: str,
    peer_id: str
) -> bool:
    """Store subagent result to Honcho."""
    if not HONCHO_AVAILABLE:
        return False

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})

        # Create a session for subagent tracking
        session_id = "subagent-results"
        session = client.session(session_id)

        # Build message
        message_lines = [
            f"[SUBAGENT] {agent_type}",
            f"Description: {description}",
            f"Timestamp: {datetime.now().isoformat()}"
        ]

        if learnings:
            message_lines.append("\nKey Learnings:")
            for i, learning in enumerate(learnings, 1):
                message_lines.append(f"{i}. {learning}")

        message_content = "\n".join(message_lines)

        msg = peer.message(message_content)
        session.add_messages([msg])

        return True

    except Exception as e:
        print(f"[Honcho] Failed to store subagent result: {e}", file=sys.stderr)
        return False


def process_subagent_stop(agent_type: str, description: str, result: dict) -> dict:
    """
    Process subagent stop event.

    Args:
        agent_type: Type of subagent
        description: Task description
        result: Result from the subagent

    Returns:
        Processing result
    """
    # Check if opted out
    if os.getenv("HONCHO_SESSION_OPT_OUT", "false").lower() == "true":
        return {"opted_out": True}

    # Extract learnings
    learnings = extract_learnings(result)

    # Store to Honcho
    base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")
    workspace = os.getenv("HONCHO_WORKSPACE", "default")
    peer_id = os.getenv("HONCHO_PEER_ID", "user")

    saved = store_subagent_result(
        agent_type,
        description,
        learnings,
        base_url,
        workspace,
        peer_id
    )

    return {
        "agent_type": agent_type,
        "description": description,
        "learnings_count": len(learnings),
        "learnings": learnings,
        "saved": saved
    }


def main():
    """Main entry point for the hook."""
    # Subagent info may come from environment variables or stdin
    agent_type = os.getenv("HONCHO_SUBAGENT_TYPE", "")
    description = os.getenv("HONCHO_SUBAGENT_DESCRIPTION", "")
    result_str = os.getenv("HONCHO_SUBAGENT_RESULT", "{}")

    if not agent_type and not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            agent_type = data.get("agent_type", "")
            description = data.get("description", "")
            result_str = data.get("result", "{}")
        except json.JSONDecodeError:
            pass

    # If no info, just show status
    if not agent_type:
        print("[Honcho] SubagentStop hook ready")
        print("  Will track subagent usage and results")
        return

    try:
        result = json.loads(result_str) if isinstance(result_str, str) else result_str
    except json.JSONDecodeError:
        result = {}

    process_result = process_subagent_stop(agent_type, description, result)

    if process_result.get("opted_out"):
        print("[Honcho] Session opted out of subagent tracking")
        return

    learnings_count = process_result.get("learnings_count", 0)
    saved = process_result.get("saved", False)

    print(f"[Honcho] Subagent '{agent_type}' completed")
    if learnings_count > 0:
        print(f"[Honcho] Extracted {learnings_count} learning(s)")
    if saved:
        print("[Honcho] Results saved to memory")


if __name__ == "__main__":
    main()
