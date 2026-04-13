#!/usr/bin/env python3
"""
SessionStart hook: Load user's memory from Honcho.

Displays observations about the user at session start.
"""

import os
import sys

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


def load_user_memory() -> str:
    """Load and format user memory from Honcho."""
    if not HONCHO_AVAILABLE:
        return "[Honcho] honcho-ai not installed. Run: pip install honcho-ai"

    workspace = os.getenv("HONCHO_WORKSPACE", "default")
    peer_id = os.getenv("HONCHO_PEER_ID", "user")
    base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id)

        # Query for observations about the user
        response = peer.chat("What do you know about this user? Summarize briefly.")

        if response and "don't have any information" not in response.lower():
            return f"[Honcho Memory] Loaded for: {peer_id}\n\n{response}"
        else:
            return f"[Honcho] No observations yet for {peer_id}. Memories will build over time."

    except Exception as e:
        return f"[Honcho] Connection failed: {e}"


if __name__ == "__main__":
    print(load_user_memory())
