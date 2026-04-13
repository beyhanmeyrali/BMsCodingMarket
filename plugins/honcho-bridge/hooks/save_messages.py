#!/usr/bin/env python3
"""
SessionEnd hook: Save session messages to Honcho.

Stores conversation for future observation extraction.
"""

import os
import sys

try:
    from honcho import Honcho as HonchoClient
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False


def save_session_messages(messages: list) -> int:
    """
    Save session messages to Honcho.

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Number of messages stored
    """
    if not HONCHO_AVAILABLE:
        print("[Honcho] honcho-ai not installed. Run: pip install honcho-ai")
        return 0

    workspace = os.getenv("HONCHO_WORKSPACE", "default")
    peer_id = os.getenv("HONCHO_PEER_ID", "user")
    base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")

    if not messages:
        return 0

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        # Get or create peers
        user_peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})
        assistant_peer = client.peer("assistant", metadata={"name": "Assistant", "peer_type": "agent"})

        # Create or get session
        import datetime
        session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        session = client.session(session_id)

        # Store messages
        message_objects = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                message_objects.append(user_peer.message(content))
            elif role == "assistant":
                message_objects.append(assistant_peer.message(content))

        if message_objects:
            session.add_messages(message_objects)
            return len(message_objects)

    except Exception as e:
        print(f"[Honcho] Failed to save: {e}")
        return 0


if __name__ == "__main__":
    # Messages will be passed by Claude Code via stdin or env
    # For now, this is a placeholder for the hook system
    print("[Honcho] SessionEnd hook: Messages will be stored on session end")
