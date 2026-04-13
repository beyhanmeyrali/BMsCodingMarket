#!/usr/bin/env python3
"""
Store a session summary into Honcho memory.

Called by the opencode plugin hook after each agent session.

Usage:
    python store_to_honcho.py --session-id <id> --summary <text> [--peer <id>] [--workspace <id>]
"""

import sys
import argparse

try:
    from honcho import Honcho
except ImportError:
    print(
        "[honcho-memory] ERROR: honcho-ai not installed. Run: pip install honcho-ai",
        file=sys.stderr,
    )
    sys.exit(1)

HONCHO_BASE_URL = "http://localhost:8000"
DEFAULT_WORKSPACE = "bms-coding-market"
DEFAULT_PEER = "dev"


def store(session_id: str, summary: str, peer_id: str, workspace_id: str) -> None:
    client = Honcho(
        base_url=HONCHO_BASE_URL,
        api_key="placeholder",
        workspace_id=workspace_id,
    )

    peer = client.peer(peer_id)
    session = client.session(f"opencode-{session_id}")
    session.add_messages([peer.message(summary)])
    print(
        f"[honcho-memory] Stored summary for session opencode-{session_id} (peer={peer_id}, workspace={workspace_id})"
    )


def main():
    parser = argparse.ArgumentParser(description="Store session summary to Honcho")
    parser.add_argument("--session-id", required=True, help="opencode session ID")
    parser.add_argument("--summary", required=True, help="Summary text to store")
    parser.add_argument(
        "--peer", default=DEFAULT_PEER, help=f"Honcho peer ID (default: {DEFAULT_PEER})"
    )
    parser.add_argument(
        "--workspace",
        default=DEFAULT_WORKSPACE,
        help=f"Honcho workspace (default: {DEFAULT_WORKSPACE})",
    )

    args = parser.parse_args()

    if not args.summary.strip():
        print("[honcho-memory] Empty summary, skipping.", file=sys.stderr)
        sys.exit(0)

    store(
        session_id=args.session_id,
        summary=args.summary,
        peer_id=args.peer,
        workspace_id=args.workspace,
    )


if __name__ == "__main__":
    main()
