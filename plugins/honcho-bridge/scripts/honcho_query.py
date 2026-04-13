#!/usr/bin/env python3
"""
Query Honcho memory using peer.chat().

Retrieves learned information about a user from previous conversations.
"""

import sys
import argparse
import os
from pathlib import Path
from typing import Optional

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


def query_honcho(
    base_url: str,
    workspace: str,
    peer_id: str,
    query: str,
) -> str:
    """Query Honcho memory for information about a peer."""
    if not HONCHO_AVAILABLE:
        raise ImportError("honcho-ai not installed. Run: pip install honcho-ai")

    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    peer = client.peer(peer_id)

    response = peer.chat(query)

    return response


def main():
    parser = argparse.ArgumentParser(
        description="Query Honcho memory using peer.chat()"
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
        "--query",
        "-q",
        required=True,
        help="Question to ask about the peer",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Honcho Memory Query")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print(f"Query: {args.query}")
    print("-" * 60)

    try:
        response = query_honcho(
            base_url=args.base_url,
            workspace=args.workspace,
            peer_id=args.peer,
            query=args.query,
        )

        print(f"\n{response}")
        print("\n" + "=" * 60)
        print("[SUCCESS] Query complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Query failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
