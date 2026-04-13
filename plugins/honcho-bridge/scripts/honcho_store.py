#!/usr/bin/env python3
"""
Store messages to Honcho memory.

Captures important information for future recall.
"""

import sys
import argparse
import os
from pathlib import Path
from typing import List

# Fix Windows encoding issue
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


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


# Load .env config at module level
load_env_config()

try:
    from honcho import Honcho as HonchoClient
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False


def store_messages(
    base_url: str,
    workspace: str,
    peer_id: str,
    session_id: str,
    messages: List[str],
    peer_name: str = None,
    peer_type: str = "user",
) -> int:
    """Store messages to Honcho memory."""
    if not HONCHO_AVAILABLE:
        raise ImportError("honcho-ai not installed. Run: pip install honcho-ai")

    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    # Create peer
    peer_metadata = {"peer_type": peer_type}
    if peer_name:
        peer_metadata["name"] = peer_name

    peer = client.peer(peer_id, metadata=peer_metadata)

    # Create session
    session = client.session(session_id)

    # Store messages
    message_objects = [peer.message(msg) for msg in messages]
    session.add_messages(message_objects)

    return len(messages)


def main():
    parser = argparse.ArgumentParser(
        description="Store messages to Honcho memory"
    )
    parser.add_argument(
        "--base-url",
        "-b",
        default=os.getenv("HONCHO_BASE_URL", "http://localhost:8000"),
        help="Honcho server URL",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        default=os.getenv("HONCHO_WORKSPACE", "default"),
        help="Workspace ID (default: from .env or 'default')",
    )
    parser.add_argument(
        "--peer",
        "-p",
        default=os.getenv("HONCHO_PEER_ID", "user"),
        help="Peer ID (default: from .env or 'user')",
    )
    parser.add_argument(
        "--peer-name",
        help="Peer display name",
    )
    parser.add_argument(
        "--peer-type",
        default="user",
        help="Peer type (default: user)",
    )
    parser.add_argument(
        "--session",
        "-s",
        default=os.getenv("HONCHO_SESSION", "manual"),
        help="Session ID (default: 'manual')",
    )
    parser.add_argument(
        "--message",
        "-m",
        action="append",
        help="Message content (can be specified multiple times)",
    )

    args = parser.parse_args()

    if not args.message:
        print("[ERROR] At least one --message is required")
        sys.exit(1)

    print("=" * 60)
    print("Honcho Memory Store")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print(f"Session: {args.session}")
    print(f"Messages: {len(args.message)}")
    print("-" * 60)

    try:
        count = store_messages(
            base_url=args.base_url,
            workspace=args.workspace,
            peer_id=args.peer,
            session_id=args.session,
            messages=args.message,
            peer_name=args.peer_name,
            peer_type=args.peer_type,
        )

        print(f"\nStored {count} message(s)")
        print("\n" + "=" * 60)
        print("[SUCCESS] Messages stored!")
        print("\nNote: The deriver will process these messages in ~1 minute")
        print("and extract observations. Then use honcho-query to retrieve.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Store failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
