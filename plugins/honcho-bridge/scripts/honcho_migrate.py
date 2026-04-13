#!/usr/bin/env python3
"""
Migrate data between Honcho workspaces.

Copy or move peers, sessions, and messages.
"""

import sys
import argparse
from typing import Optional

try:
    from honcho import Honcho as HonchoClient
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False


def preview_migration(
    base_url: str,
    source_workspace: str,
    dest_workspace: str,
    peer_id: Optional[str] = None,
) -> dict:
    """Preview what would be migrated."""
    source_client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=source_workspace
    )

    peers_to_migrate = []
    if peer_id:
        peer = source_client.peer(peer_id)
        peers_to_migrate.append(peer)
    else:
        peers_to_migrate = list(source_client.peers())

    session_count = 0
    message_count = 0

    for peer in peers_to_migrate:
        for session in peer.sessions():
            session_count += 1
            messages = list(session.messages())
            message_count += len(messages)

    return {
        "peer_count": len(peers_to_migrate),
        "session_count": session_count,
        "message_count": message_count,
        "peers": [p.id for p in peers_to_migrate],
    }


def migrate_data(
    base_url: str,
    source_workspace: str,
    dest_workspace: str,
    mode: str = "copy",
    peer_id: Optional[str] = None,
) -> dict:
    """Actually migrate data between workspaces."""
    source_client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=source_workspace
    )

    dest_client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=dest_workspace
    )

    peers_to_migrate = []
    if peer_id:
        peer = source_client.peer(peer_id)
        peers_to_migrate.append(peer)
    else:
        peers_to_migrate = list(source_client.peers())

    migrated_peers = 0
    migrated_sessions = 0
    migrated_messages = 0

    for source_peer in peers_to_migrate:
        # Get peer metadata
        peer_metadata = {}
        if hasattr(source_peer, 'metadata'):
            peer_metadata = source_peer.metadata or {}

        # Create peer in destination
        dest_peer = dest_client.peer(source_peer.id, metadata=peer_metadata)

        # Migrate sessions
        for source_session in source_peer.sessions():
            session_metadata = {}
            if hasattr(source_session, 'metadata'):
                session_metadata = source_session.metadata or {}

            dest_session = dest_client.session(source_session.id, metadata=session_metadata)

            # Migrate messages
            messages = list(source_session.messages())
            message_objects = []
            for msg in messages:
                message_objects.append(dest_peer.message(msg.content))

            dest_session.add_messages(message_objects)
            migrated_sessions += 1
            migrated_messages += len(messages)

        migrated_peers += 1

        # Delete from source if mode is move
        if mode == "move":
            for source_session in source_peer.sessions():
                messages = list(source_session.messages())
                for msg in messages:
                    try:
                        msg.delete()
                    except Exception:
                        pass
                try:
                    source_session.delete()
                except Exception:
                    pass
            try:
                source_peer.delete()
            except Exception:
                pass

    return {
        "migrated_peers": migrated_peers,
        "migrated_sessions": migrated_sessions,
        "migrated_messages": migrated_messages,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Migrate data between Honcho workspaces"
    )
    parser.add_argument(
        "--base-url",
        "-b",
        default="http://localhost:8000",
        help="Honcho server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--source",
        "-s",
        required=True,
        help="Source workspace ID",
    )
    parser.add_argument(
        "--destination",
        "-d",
        required=True,
        help="Destination workspace ID",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["copy", "move"],
        default="copy",
        help="Migration mode: copy (keep source) or move (delete source)",
    )
    parser.add_argument(
        "--peer",
        "-p",
        help="Migrate only this specific peer ID",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only, don't actually migrate",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("HONCHO WORKSPACE MIGRATION")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Destination: {args.destination}")
    print(f"Mode: {args.mode}")
    if args.peer:
        print(f"Peer filter: {args.peer}")
    print()

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print("-" * 60)

    try:
        preview = preview_migration(
            base_url=args.base_url,
            source_workspace=args.source,
            dest_workspace=args.destination,
            peer_id=args.peer,
        )

        print(f"Peers to migrate: {preview['peer_count']}")
        print(f"Sessions to migrate: {preview['session_count']}")
        print(f"Messages to migrate: {preview['message_count']}")
        print()

        if args.dry_run:
            print("=" * 60)
            print("DRY RUN COMPLETE - No changes made")
            print("=" * 60)
            sys.exit(0)

        if not args.yes:
            response = input(f"Confirm {args.mode} from '{args.source}' to '{args.destination}'? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Aborted.")
                sys.exit(0)

        print("-" * 60)
        result = migrate_data(
            base_url=args.base_url,
            source_workspace=args.source,
            dest_workspace=args.destination,
            mode=args.mode,
            peer_id=args.peer,
        )

        print(f"Migrated peers: {result['migrated_peers']}")
        print(f"Migrated sessions: {result['migrated_sessions']}")
        print(f"Migrated messages: {result['migrated_messages']}")
        print()
        print("=" * 60)
        print("[SUCCESS] Migration complete!")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
