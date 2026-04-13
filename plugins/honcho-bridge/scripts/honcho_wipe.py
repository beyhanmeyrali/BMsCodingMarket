#!/usr/bin/env python3
"""
Wipe all data from a Honcho workspace.

DESTRUCTIVE ACTION - Deletes peers, sessions, messages, observations.
"""

import sys
import argparse

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


def preview_wipe(
    base_url: str,
    workspace: str,
) -> dict:
    """Preview what would be deleted."""
    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    peers = list(client.peers())
    peer_count = len(peers)

    session_count = 0
    message_count = 0

    for peer in peers:
        for session in peer.sessions():
            session_count += 1
            messages = list(session.messages())
            message_count += len(messages)

    return {
        "peer_count": peer_count,
        "session_count": session_count,
        "message_count": message_count,
    }


def wipe_workspace(
    base_url: str,
    workspace: str,
) -> dict:
    """Actually delete all data from workspace."""
    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    deleted_peers = 0
    deleted_sessions = 0
    deleted_messages = 0

    peers = list(client.peers())

    for peer in peers:
        for session in peer.sessions():
            # Delete messages first
            messages = list(session.messages())
            for msg in messages:
                try:
                    msg.delete()
                    deleted_messages += 1
                except Exception:
                    pass  # May cascade delete
            deleted_sessions += 1

        # Delete peer
        try:
            peer.delete()
            deleted_peers += 1
        except Exception:
            pass  # May cascade delete

    return {
        "deleted_peers": deleted_peers,
        "deleted_sessions": deleted_sessions,
        "deleted_messages": deleted_messages,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Wipe all data from a Honcho workspace (DESTRUCTIVE)"
    )
    parser.add_argument(
        "--base-url",
        "-b",
        default="http://localhost:8000",
        help="Honcho server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        required=True,
        help="Workspace ID to wipe",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the deletion (without this, just preview)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("HONCHO WORKSPACE WIPE")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print()

    if not args.confirm:
        print("PREVIEW MODE - No changes will be made")
        print("-" * 60)

        try:
            preview = preview_wipe(
                base_url=args.base_url,
                workspace=args.workspace,
            )

            print(f"Peers to delete: {preview['peer_count']}")
            print(f"Sessions to delete: {preview['session_count']}")
            print(f"Messages to delete: {preview['message_count']}")
            print()
            print("=" * 60)
            print("To actually delete, add --confirm flag")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] Preview failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    else:
        print("[!] DESTRUCTIVE ACTION - Data will be permanently deleted!")
        print("-" * 60)

        try:
            result = wipe_workspace(
                base_url=args.base_url,
                workspace=args.workspace,
            )

            print(f"Deleted peers: {result['deleted_peers']}")
            print(f"Deleted sessions: {result['deleted_sessions']}")
            print(f"Deleted messages: {result['deleted_messages']}")
            print()
            print("=" * 60)
            print("[SUCCESS] Workspace wiped!")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] Wipe failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
