#!/usr/bin/env python3
"""
Honcho to Wiki Export Script

Exports honcho-local JSON storage to LLM Wiki markdown format.
Compatible with Karpathy's LLM Wiki pattern.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add lib path for honcho import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from local_honcho import LocalHoncho
except ImportError:
    print("[WARNING] local_honcho not found. This script can still export JSON files.")


def load_honcho_storage(storage_path: str) -> Dict[str, Any]:
    """Load honcho JSON storage file."""
    path = Path(storage_path)
    if not path.exists():
        print(f"[ERROR] Storage file not found: {storage_path}")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def sanitize_filename(name: str) -> str:
    """Sanitize a name for use as a filename."""
    # Replace invalid characters with underscores
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, '_')
    return name


def escape_yaml(value: str) -> str:
    """Escape special characters for YAML."""
    if not isinstance(value, str):
        return str(value)
    # Escape quotes and backslashes
    return value.replace('\\', '\\\\').replace('"', '\\"')


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp for display."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return ts


def create_peer_page(peer_id: str, peer_data: Dict, representation: Dict, workspace: str, sessions: List) -> str:
    """Create markdown content for a peer page."""
    peer_type = peer_data.get('peer_type', 'user')
    name = peer_data.get('name', peer_id)
    created_at = peer_data.get('created_at', '')

    # Count sessions this peer participated in
    peer_sessions = [s for s in sessions if peer_id in s.get('participants', [])]

    # Extract representation data
    interests = representation.get('interests', [])
    comm_style = representation.get('communication_style', 'Not available')
    topics = representation.get('frequent_topics', [])
    sentiment = representation.get('sentiment', 'neutral')

    # Build session links
    session_links = []
    for session in peer_sessions:
        session_id = session.get('id', '')
        title = session.get('title', f"Conversation from {format_timestamp(session.get('created_at', ''))}")
        session_links.append(f"- [[{session_id}]] - {title}")

    content = f"""---
peer_id: {escape_yaml(peer_id)}
name: {escape_yaml(name)}
peer_type: {escape_yaml(peer_type)}
created_at: {escape_yaml(created_at)}
workspace: {escape_yaml(workspace)}
session_count: {len(peer_sessions)}
last_active: {escape_yaml(format_timestamp(created_at))}
---

# {name}

**Type:** {peer_type.capitalize()}
**Created:** {format_timestamp(created_at)}
**Sessions:** {len(peer_sessions)}

## Profile

{representation.get('raw_response', f'### Communication Style\\n{comm_style}\\n### Sentiment\\n{sentiment}') if 'raw_response' in representation else f'### Communication Style\\n{comm_style}\\n\\n### Sentiment\\n{sentiment}'}

"""

    if interests:
        content += "### Interests\\n\\n"
        for interest in interests:
            content += f"- {interest}\\n"
        content += "\\n"

    if topics:
        content += "### Frequent Topics\\n\\n"
        for topic in topics:
            content += f"- {topic}\\n"
        content += "\\n"

    if peer_sessions:
        content += "## Sessions\\n\\n"
        content += "\\n".join(session_links)
        content += "\\n"

    return content


def create_session_page(session_id: str, messages: List[Dict], peers: Dict, workspace: str, metadata: Dict = None) -> str:
    """Create markdown content for a session page."""
    metadata = metadata or {}
    title = metadata.get('title', f"Conversation - {session_id}")
    created_at = messages[0].get('timestamp', '') if messages else ''

    # Get participants
    participant_ids = set()
    for msg in messages:
        peer_id = msg.get('metadata', {}).get('peer_id', '')
        if peer_id:
            participant_ids.add(peer_id)

    # Build participant list
    participants_list = []
    for peer_id in participant_ids:
        peer_data = peers.get(f"{workspace}:{peer_id}", {})
        name = peer_data.get('name', peer_id)
        role = peer_data.get('peer_type', 'user')
        participants_list.append(f"- **{name}** ({role}) - [[{peer_id}]]")

    # Build transcript
    transcript_lines = []
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        timestamp = format_timestamp(msg.get('timestamp', ''))
        peer_id = msg.get('metadata', {}).get('peer_id', '')
        peer_data = peers.get(f"{workspace}:{peer_id}", {})
        peer_name = peer_data.get('name', peer_id)

        transcript_lines.append(f"### {timestamp}\\n")
        transcript_lines.append(f"**{peer_name}** ({role}):\\n")
        transcript_lines.append(f"{content}\\n")

    # Extract topics from first few messages
    topics = []
    for msg in messages[:5]:
        words = msg.get('content', '').lower().split()
        # Simple keyword extraction (could be improved with NLP)
        for word in words:
            if len(word) > 5 and word.isalpha():
                topics.append(word.capitalize())

    content = f"""---
session_id: {escape_yaml(session_id)}
title: {escape_yaml(title)}
created_at: {escape_yaml(created_at)}
workspace: {escape_yaml(workspace)}
message_count: {len(messages)}
participants: {list(participant_ids)}
---

# {title}

## Summary

{metadata.get('summary', 'Conversation log from honcho memory.')}

## Participants

{chr(10).join(participants_list)}

## Transcript

{chr(10).join(transcript_lines)}

"""

    if topics:
        unique_topics = sorted(set(topics))[:10]
        content += "## Topics\\n\\n"
        for topic in unique_topics:
            content += f"- {topic}\\n"

    return content


def create_index(peers: List, sessions: List, workspace: str, stats: Dict) -> str:
    """Create wiki index page."""
    peer_count = len(peers)
    session_count = len(sessions)
    message_count = stats.get('messages', 0)
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""---
title: Honcho Wiki Index
workspace: {escape_yaml(workspace)}
exported_at: {escape_yaml(export_time)}
---

# Honcho Wiki Index

**Workspace:** {workspace}
**Exported:** {export_time}

## Statistics

- **Total Peers:** {peer_count}
- **Total Sessions:** {session_count}
- **Total Messages:** {message_count}

## Peers

"""

    # Peer catalog
    for peer in peers:
        peer_id = peer.get('peer_id', '')
        name = peer.get('name', peer_id)
        peer_type = peer.get('peer_type', 'user')
        session_count = peer.get('session_count', 0)
        content += f"### [[{peer_id}]]\\n\\n"
        content += f"**Type:** {peer_type}\\n"
        content += f"**Sessions:** {session_count}\\n\\n"

    content += "## Sessions\\n\\n"

    # Session catalog
    for session in sessions:
        session_id = session.get('session_id', '')
        title = session.get('title', session_id)
        count = session.get('message_count', 0)
        created = session.get('created_at', '')
        content += f"### [[{session_id}]]\\n\\n"
        content += f"{title} ({count} messages)\\n"
        content += f"*Created: {format_timestamp(created)}*\\n\\n"

    return content


def append_log(workspace: str, stats: Dict, output_dir: str) -> None:
    """Append export entry to log.md."""
    log_path = Path(output_dir) / "log.md"
    export_time = datetime.now().isoformat()
    date_str = datetime.now().strftime("%Y-%m-%d")

    entry = f"""
## [{date_str}] export | honcho-to-wiki

**Workspace:** {workspace}
**Peers exported:** {stats.get('peers', 0)}
**Sessions exported:** {stats.get('sessions', 0)}
**Messages exported:** {stats.get('messages', 0)}
**Output directory:** {output_dir}
**Timestamp:** {export_time}

---

"""

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry)


def export_honcho_to_wiki(
    storage_path: str,
    output_dir: str,
    workspace: str = None,
    include_messages: bool = True,
) -> int:
    """
    Export honcho storage to wiki format.

    Args:
        storage_path: Path to honco_*.json file
        output_dir: Output directory for wiki files
        workspace: Workspace ID (auto-detected from filename if None)
        include_messages: Include full message content

    Returns:
        Number of files created
    """
    # Load storage
    storage = load_honcho_storage(storage_path)

    # Auto-detect workspace from filename
    if workspace is None:
        filename = Path(storage_path).stem
        workspace = filename.replace('honco_', '', 1)

    # Create output directory
    wiki_path = Path(output_dir)
    wiki_path.mkdir(parents=True, exist_ok=True)
    (wiki_path / "peers").mkdir(exist_ok=True)
    (wiki_path / "sessions").mkdir(exist_ok=True)

    # Extract data
    peers_data = storage.get("peers", {})
    messages_data = storage.get("messages", {})
    representations_data = storage.get("representations", {})

    # Process peers
    peer_pages = []
    peer_session_map = {}

    for peer_key, peer_data in peers_data.items():
        peer_id = peer_data.get('id', '')
        if not peer_id:
            continue

        peer_ws, peer_id_only = peer_key.split(':', 1) if ':' in peer_key else (workspace, peer_key)

        # Get representation
        repr_key = f"{peer_key}:all"
        representation = representations_data.get(repr_key, {})

        # Count sessions
        session_count = 0
        peer_sessions = []
        for session_key, messages in messages_data.items():
            session_ws, session_id_only = session_key.split(':', 1) if ':' in session_key else (workspace, session_key)
            for msg in messages:
                msg_peer_id = msg.get('metadata', {}).get('peer_id', '')
                if msg_peer_id == peer_id_only:
                    if session_id_only not in [s.get('id', '') for s in peer_sessions]:
                        peer_sessions.append({
                            'id': session_id_only,
                            'created_at': messages[0].get('timestamp', ''),
                            'title': f"Conversation - {session_id_only}",
                        })
                    session_count += 1
                    break

        peer_data['session_count'] = session_count

        # Create peer page
        peer_content = create_peer_page(
            peer_id_only,
            peer_data,
            representation,
            workspace,
            peer_sessions,
        )

        peer_file = wiki_path / "peers" / f"{sanitize_filename(peer_id_only)}.md"
        with open(peer_file, 'w', encoding='utf-8') as f:
            f.write(peer_content)

        peer_pages.append({
            'peer_id': peer_id_only,
            'name': peer_data.get('name', peer_id_only),
            'session_count': session_count,
        })

    # Process sessions
    session_pages = []
    for session_key, messages in messages_data.items():
        session_ws, session_id_only = session_key.split(':', 1) if ':' in session_key else (workspace, session_key)

        if not messages:
            continue

        # Build participant list
        participant_ids = set()
        for msg in messages:
            peer_id = msg.get('metadata', {}).get('peer_id', '')
            if peer_id:
                participant_ids.add(peer_id)

        # Get session metadata
        session_metadata = storage.get("sessions", {}).get(session_key, {})

        # Create session page
        session_content = create_session_page(
            session_id_only,
            messages,
            peers_data,
            workspace,
            session_metadata,
        )

        session_file = wiki_path / "sessions" / f"{sanitize_filename(session_id_only)}.md"
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(session_content)

        session_pages.append({
            'session_id': session_id_only,
            'title': session_metadata.get('title', f"Conversation - {session_id_only}"),
            'message_count': len(messages),
            'created_at': messages[0].get('timestamp', ''),
            'participants': list(participant_ids),
        })

    # Create index
    index_content = create_index(peer_pages, session_pages, workspace, {
        'peers': len(peer_pages),
        'sessions': len(session_pages),
        'messages': sum(len(msgs) for msgs in messages_data.values()),
    })

    index_file = wiki_path / "index.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)

    # Append to log
    append_log(workspace, {
        'peers': len(peer_pages),
        'sessions': len(session_pages),
        'messages': sum(len(msgs) for msgs in messages_data.values()),
    }, str(wiki_path))

    return len(peer_pages) + len(session_pages) + 2  # +2 for index and log


def main():
    parser = argparse.ArgumentParser(
        description="Export honcho-local memory to LLM Wiki markdown format"
    )
    parser.add_argument(
        '--workspace', '-w',
        default='local-workspace',
        help='Workspace ID (auto-detected from filename if not specified)',
    )
    parser.add_argument(
        '--storage', '-s',
        default='honco_local-workspace.json',
        help='Path to honcho storage JSON file',
    )
    parser.add_argument(
        '--output', '-o',
        default='wiki',
        help='Output directory for wiki files',
    )
    parser.add_argument(
        '--no-messages',
        action='store_true',
        help='Exclude full message content from session pages',
    )

    args = parser.parse_args()

    # Check if storage file exists
    if not Path(args.storage).exists():
        # Try to find any honco_*.json file
        import glob
        matches = glob.glob('honco_*.json')
        if matches:
            print(f"[INFO] Using storage file: {matches[0]}")
            args.storage = matches[0]
        else:
            print(f"[ERROR] No honcho storage file found. Current directory:")
            print(f"  {os.getcwd()}")
            print("\\nRun /honcho-to-wiki from a directory containing honco_*.json")
            sys.exit(1)

    print("=" * 60)
    print("Honcho to Wiki Export")
    print("=" * 60)
    print(f"[1/4] Loading storage: {args.storage}")

    try:
        file_count = export_honcho_to_wiki(
            storage_path=args.storage,
            output_dir=args.output,
            workspace=args.workspace,
            include_messages=not args.no_messages,
        )

        print(f"[2/4] Created wiki directory: {args.output}/")
        print(f"[3/4] Generated {file_count} wiki files")
        print(f"[4/4] Updated index.md and log.md")

        print("\\n" + "=" * 60)
        print("[SUCCESS] Wiki export complete!")
        print(f"\\nNext steps:")
        print(f"  1. Open {args.output}/ in Obsidian")
        print(f"  2. Enable graph view to see connections")
        print(f"  3. Browse peer pages and session logs")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
