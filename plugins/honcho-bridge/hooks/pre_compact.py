#!/usr/bin/env python3
"""
PreCompact hook: Triggered before Claude Code compacts conversation context.

Features:
- Summarize recent exchanges before compaction
- Tag important observations
- Save summary to Honcho for future reference
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


def extract_important_points(messages: list) -> list:
    """
    Extract important points from messages before compaction.

    Looks for:
    - User decisions
    - Preferences stated
    - Technical choices made
    - Problems solved
    """
    important = []

    if not messages:
        return important

    keywords = [
        "decided", "chose", "prefer", "never", "always",
        "important", "remember", "note that",
        "fixed", "solved", "resolved", "issue",
        "use", "don't use", "avoid"
    ]

    for msg in messages:
        content = ""
        if isinstance(msg, dict):
            content = msg.get("content", "")
        elif hasattr(msg, "content"):
            content = msg.content
        elif isinstance(msg, str):
            content = msg

        content_lower = content.lower()

        # Check for important keywords
        if any(keyword in content_lower for keyword in keywords):
            # Extract the relevant sentence
            sentences = content.split(".")
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    important.append(sentence.strip())
                    break

    return important[:10]  # Limit to 10 important points


def save_compaction_summary(summary: str, base_url: str, workspace: str, peer_id: str) -> bool:
    """Save the compaction summary to Honcho."""
    if not HONCHO_AVAILABLE:
        return False

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})

        # Create a session for compaction summaries
        session_id = "compaction-summaries"
        session = client.session(session_id)

        # Store the summary
        message_content = f"[COMPACTION SUMMARY] {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{summary}"

        msg = peer.message(message_content)
        session.add_messages([msg])

        return True

    except Exception as e:
        print(f"[Honcho] Failed to save compaction summary: {e}", file=sys.stderr)
        return False


def process_pre_compact(messages: list) -> dict:
    """
    Process the pre-compaction event.

    Args:
        messages: List of messages before compaction

    Returns:
        Processing result with important points and summary
    """
    # Check if opted out
    if os.getenv("HONCHO_SESSION_OPT_OUT", "false").lower() == "true":
        return {"opted_out": True}

    # Extract important points
    important_points = extract_important_points(messages)

    # Build summary
    context = {
        "timestamp": datetime.now().isoformat(),
        "folder": Path.cwd().name,
    }

    summary_lines = [
        f"Session in {context['folder']}",
        f"Extracted {len(important_points)} important point(s)",
        ""
    ]

    if important_points:
        summary_lines.append("Important Points:")
        for i, point in enumerate(important_points, 1):
            summary_lines.append(f"{i}. {point}")

    summary = "\n".join(summary_lines)

    # Save to Honcho
    base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")
    workspace = os.getenv("HONCHO_WORKSPACE", "default")
    peer_id = os.getenv("HONCHO_PEER_ID", "user")

    saved = save_compaction_summary(summary, base_url, workspace, peer_id)

    return {
        "important_points": important_points,
        "summary": summary,
        "saved": saved,
        "context": context
    }


def main():
    """Main entry point for the hook."""
    # Messages may come from stdin or environment variable
    messages_str = os.getenv("HONCHO_MESSAGES", "[]")

    if not messages_str and not sys.stdin.isatty():
        try:
            messages_str = sys.stdin.read()
        except Exception:
            messages_str = "[]"

    try:
        messages = json.loads(messages_str) if messages_str else []
    except json.JSONDecodeError:
        messages = []

    # If no messages, just show status
    if not messages:
        print("[Honcho] PreCompact hook ready")
        print("  Will extract important points before context compaction")
        return

    result = process_pre_compact(messages)

    if result.get("opted_out"):
        print("[Honcho] Session opted out of compaction tracking")
        return

    important_count = len(result.get("important_points", []))
    saved = result.get("saved", False)

    print(f"[Honcho] Extracted {important_count} important point(s) before compaction")
    if saved:
        print("[Honcho] Summary saved to memory")


if __name__ == "__main__":
    main()
