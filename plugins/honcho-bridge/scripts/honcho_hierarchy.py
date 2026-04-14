#!/usr/bin/env python3
"""
Memory hierarchy management for Honcho.

Implements multi-level memory organization:
- Global: User preferences across all projects
- Project: Project-specific decisions and context
- File: Specific file-related knowledge
- Context: Session-specific contextual information
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

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


# Memory hierarchy levels
MEMORY_LEVELS = ["global", "project", "file", "context"]


def get_scope_id(level: str, cwd: Optional[Path] = None) -> str:
    """
    Get the scope ID for a given memory level.

    - global: "global"
    - project: current folder name
    - file: specific file path
    - context: session ID (timestamped)
    """
    if cwd is None:
        cwd = Path.cwd()

    if level == "global":
        return "global"
    elif level == "project":
        return cwd.name
    elif level == "file":
        # Caller must provide specific file
        return "unknown"
    elif level == "context":
        return datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
        return "unknown"


def create_memory_level(base_url: str, workspace: str, peer_id: str,
                       level: str, scope_id: Optional[str] = None) -> bool:
    """
    Initialize a memory level by creating a dedicated session.

    Each memory level gets its own session for isolation and querying.
    """
    if not HONCHO_AVAILABLE:
        return False

    if level not in MEMORY_LEVELS:
        print(f"[ERROR] Invalid memory level: {level}")
        return False

    if scope_id is None:
        scope_id = get_scope_id(level)

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})

        # Create a session for this memory level
        session_id = f"memory-{level}-{scope_id}"
        session = client.session(session_id)

        # Store a marker message to initialize
        marker = f"[MEMORY LEVEL] Initialized {level} memory for scope: {scope_id}"
        msg = peer.message(marker)
        session.add_messages([msg])

        print(f"[SUCCESS] Created {level} memory session: {session_id}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create memory level: {e}")
        return False


def tag_memory_level(content: str, level: str, scope_id: Optional[str] = None) -> str:
    """
    Tag a message with its memory level.

    Returns the content with level tags prepended.
    """
    if scope_id is None:
        scope_id = get_scope_id(level)

    tag = f"[{level.upper()}]"

    if scope_id and level != "global":
        tag += f" [{scope_id}]"

    return f"{tag} {content}"


def store_at_level(base_url: str, workspace: str, peer_id: str,
                  level: str, content: str, scope_id: Optional[str] = None,
                  metadata: Optional[Dict] = None) -> bool:
    """
    Store a message at a specific memory level.

    Args:
        base_url: Honcho server URL
        workspace: Workspace ID
        peer_id: Peer ID
        level: Memory level (global, project, file, context)
        content: Message content
        scope_id: Optional scope identifier (e.g., file path, project name)
        metadata: Optional additional metadata

    Returns:
        True if stored successfully
    """
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed")
        return False

    if level not in MEMORY_LEVELS:
        print(f"[ERROR] Invalid memory level: {level}")
        return False

    if scope_id is None:
        scope_id = get_scope_id(level)

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})

        # Use level-specific session
        session_id = f"memory-{level}-{scope_id}"
        session = client.session(session_id)

        # Tag content with level
        tagged_content = tag_memory_level(content, level, scope_id)

        # Add metadata
        msg_metadata = {
            "memory_level": level,
            "scope_id": scope_id,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            msg_metadata.update(metadata)

        # Store the message
        msg = peer.message(tagged_content)
        session.add_messages([msg])

        return True

    except Exception as e:
        print(f"[ERROR] Failed to store at level {level}: {e}")
        return False


def query_by_level(base_url: str, workspace: str, peer_id: str,
                  level: str, scope_id: Optional[str] = None,
                  query: Optional[str] = None) -> List[str]:
    """
    Query observations at a specific memory level.

    Args:
        base_url: Honcho server URL
        workspace: Workspace ID
        peer_id: Peer ID
        level: Memory level to query
        scope_id: Optional scope identifier
        query: Optional query string

    Returns:
        List of observation strings
    """
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed")
        return []

    if scope_id is None:
        scope_id = get_scope_id(level)

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id)

        # Build query for specific level
        if query:
            search_query = f"What do you know about {query}? Focus on {level} level information."
        else:
            search_query = f"What do you know at the {level} memory level?"

        response = peer.chat(search_query)

        if response and "don't have any information" not in response.lower():
            return [response]

        return []

    except Exception as e:
        print(f"[ERROR] Failed to query level {level}: {e}")
        return []


def query_all_levels(base_url: str, workspace: str, peer_id: str,
                     query: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Query all memory levels and return organized results.

    Returns a dict mapping level names to result lists.
    """
    results = {}

    for level in MEMORY_LEVELS:
        results[level] = query_by_level(base_url, workspace, peer_id, level, query=query)

    return results


def move_memory(base_url: str, workspace: str, peer_id: str,
               content: str, from_level: str, to_level: str,
               from_scope: Optional[str] = None, to_scope: Optional[str] = None) -> bool:
    """
    Move a memory from one level to another.

    Useful for promoting project-specific decisions to global rules, etc.
    """
    # Store at new level
    success = store_at_level(base_url, workspace, peer_id, to_level, content, to_scope)

    if success:
        print(f"[SUCCESS] Moved memory from {from_level} to {to_level}")

    return success


def list_memory_levels(base_url: str, workspace: str, peer_id: str) -> Dict[str, int]:
    """
    List all memory levels and their observation counts.

    Returns a dict mapping level names to counts.
    """
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed")
        return {}

    counts = {level: 0 for level in MEMORY_LEVELS}

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id)

        # Count sessions/observations at each level
        for session in peer.sessions():
            session_id = session.id
            if session_id.startswith("memory-"):
                # Parse the level from session ID
                parts = session_id.split("-", 2)
                if len(parts) >= 2:
                    level = parts[1]
                    if level in counts:
                        # Count messages in this session
                        messages = list(session.messages())
                        counts[level] += len(messages)

    except Exception as e:
        print(f"[ERROR] Failed to list memory levels: {e}")

    return counts


def main():
    """CLI for memory hierarchy management."""
    parser = argparse.ArgumentParser(
        description="Manage Honcho memory hierarchy"
    )
    parser.add_argument(
        "--base-url", "-b",
        default=os.getenv("HONCHO_BASE_URL", "http://localhost:8000"),
        help="Honcho server URL"
    )
    parser.add_argument(
        "--workspace", "-w",
        default=os.getenv("HONCHO_WORKSPACE", "default"),
        help="Workspace ID"
    )
    parser.add_argument(
        "--peer", "-p",
        default=os.getenv("HONCHO_PEER_ID", "user"),
        help="Peer ID"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create level command
    create_parser = subparsers.add_parser("create", help="Create a memory level")
    create_parser.add_argument("level", choices=MEMORY_LEVELS, help="Memory level to create")
    create_parser.add_argument("--scope", "-s", help="Scope identifier")

    # Store command
    store_parser = subparsers.add_parser("store", help="Store at a memory level")
    store_parser.add_argument("level", choices=MEMORY_LEVELS, help="Memory level")
    store_parser.add_argument("content", help="Content to store")
    store_parser.add_argument("--scope", "-s", help="Scope identifier")
    store_parser.add_argument("--metadata", "-m", help="JSON metadata")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query a memory level")
    query_parser.add_argument("level", nargs="?", choices=MEMORY_LEVELS, help="Memory level (omit for all)")
    query_parser.add_argument("--scope", "-s", help="Scope identifier")
    query_parser.add_argument("--search", "-q", help="Search query")

    # List command
    list_parser = subparsers.add_parser("list", help="List all memory levels")

    # Move command
    move_parser = subparsers.add_parser("move", help="Move between levels")
    move_parser.add_argument("from_level", choices=MEMORY_LEVELS, help="Source level")
    move_parser.add_argument("to_level", choices=MEMORY_LEVELS, help="Target level")
    move_parser.add_argument("content", help="Content to move")
    move_parser.add_argument("--from-scope", help="Source scope")
    move_parser.add_argument("--to-scope", help="Target scope")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print("=" * 60)
    print("Honcho Memory Hierarchy")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print("-" * 60)

    try:
        if args.command == "create":
            create_memory_level(
                args.base_url, args.workspace, args.peer,
                args.level, args.scope
            )

        elif args.command == "store":
            import json
            metadata = json.loads(args.metadata) if args.metadata else None
            success = store_at_level(
                args.base_url, args.workspace, args.peer,
                args.level, args.content, args.scope, metadata
            )
            if success:
                print(f"[SUCCESS] Stored at {args.level} level")

        elif args.command == "query":
            if args.level:
                results = query_by_level(
                    args.base_url, args.workspace, args.peer,
                    args.level, args.scope, args.search
                )
                if results:
                    for r in results:
                        print(r)
                else:
                    print(f"[INFO] No results for {args.level} level")
            else:
                results = query_all_levels(
                    args.base_url, args.workspace, args.peer,
                    args.search
                )
                for level, items in results.items():
                    if items:
                        print(f"\n## {level.upper()}")
                        for item in items:
                            print(item)

        elif args.command == "list":
            counts = list_memory_levels(
                args.base_url, args.workspace, args.peer
            )
            print("\nMemory Levels:")
            for level, count in counts.items():
                print(f"  {level}: {count} observation(s)")

        elif args.command == "move":
            move_memory(
                args.base_url, args.workspace, args.peer,
                args.content, args.from_level, args.to_level,
                args.from_scope, args.to_scope
            )

    except Exception as e:
        print(f"\n[ERROR] Command failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
