#!/usr/bin/env python3
"""
Wiki to Honcho Import Script

Imports LLM Wiki markdown files into honcho-local JSON storage format.
Converts Obsidian vaults to agent memory.
"""

import os
import sys
import re
import yaml
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


def convert_datetime_to_string(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetime_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    return obj


def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML frontmatter from markdown content."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError as e:
            print(f"[WARNING] Failed to parse YAML: {e}")
            return None, content
    return None, content


def parse_peer_page(file_path: Path) -> Optional[Dict]:
    """Parse a peer wiki page into honcho peer data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        print(f"[WARNING] No frontmatter in {file_path.name}, skipping")
        return None

    peer_id = frontmatter.get('peer_id', file_path.stem)
    name = frontmatter.get('name', peer_id)
    peer_type = frontmatter.get('peer_type', 'user')

    return {
        'id': peer_id,
        'name': name,
        'peer_type': peer_type,
        'metadata': frontmatter,
        'body': body
    }


def extract_messages_from_transcript(body: str, participant_map: Dict[str, str]) -> List[Dict]:
    """Extract messages from transcript section."""
    messages = []
    in_transcript = False

    for line in body.split('\n'):
        line_stripped = line.strip()

        # Find transcript section
        if line_stripped == '## Transcript':
            in_transcript = True
            continue

        if not in_transcript:
            continue

        # Parse timestamped messages
        if line_stripped.startswith('### '):
            continue  # Skip timestamp header

        # Format: **name** (role): content
        match = re.match(r'\*\*([^*]+)\*\*\s*\(([^)]+)\):\s*(.*)', line_stripped)
        if match:
            name = match.group(1).strip()
            role = match.group(2).strip()
            content = match.group(3).strip()

            # Map display name to peer_id
            peer_id = participant_map.get(name, name)

            messages.append({
                'role': role,
                'content': content,
                'metadata': {'peer_id': peer_id},
                'timestamp': datetime.now().isoformat()
            })

    return messages


def parse_session_page(file_path: Path, participant_map: Dict[str, str]) -> Optional[Dict]:
    """Parse a session wiki page into honcho session data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        print(f"[WARNING] No frontmatter in {file_path.name}, skipping")
        return None

    session_id = frontmatter.get('session_id', file_path.stem)

    # Extract messages from transcript
    messages = extract_messages_from_transcript(body, participant_map)

    return {
        'id': session_id,
        'metadata': frontmatter,
        'messages': messages
    }


def import_wiki_to_honcho(
    wiki_path: str,
    output_file: str,
    workspace: str = 'imported-wiki',
) -> int:
    """
    Import wiki markdown files into honcho JSON format.

    Args:
        wiki_path: Path to wiki directory
        output_file: Output honcho JSON file
        workspace: Workspace ID for imported data

    Returns:
        Number of peers and sessions imported
    """
    wiki_dir = Path(wiki_path)

    if not wiki_dir.exists():
        print(f"[ERROR] Wiki directory not found: {wiki_path}")
        return 0

    # Find all markdown files
    peer_files = list(wiki_dir.glob("peers/*.md"))
    session_files = list(wiki_dir.glob("sessions/*.md"))

    print(f"[INFO] Found {len(peer_files)} peer files")
    print(f"[INFO] Found {len(session_files)} session files")

    # Initialize storage
    storage = {
        'workspaces': {},
        'peers': {},
        'sessions': {},
        'messages': {},
        'representations': {}
    }

    # Import peers
    peer_count = 0
    peer_map = {}  # Maps display names to peer_ids

    for peer_file in peer_files:
        peer_data = parse_peer_page(peer_file)
        if peer_data:
            peer_key = f"{workspace}:{peer_data['id']}"
            # Convert datetime to string for JSON serialization
            peer_data_clean = convert_datetime_to_string(peer_data)
            storage['peers'][peer_key] = peer_data_clean
            peer_map[peer_data['name']] = peer_data['id']
            peer_count += 1

    # Import sessions
    session_count = 0
    message_count = 0

    for session_file in session_files:
        session_data = parse_session_page(session_file, peer_map)
        if session_data:
            session_key = f"{workspace}:{session_data['id']}"

            # Convert all datetime objects to strings for JSON serialization
            session_data_clean = convert_datetime_to_string(session_data)
            storage['sessions'][session_key] = session_data_clean.get('metadata', {})
            storage['messages'][session_key] = session_data_clean.get('messages', [])

            session_count += 1
            message_count += len(session_data.get('messages', []))

    # Write output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(storage, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Imported {peer_count} peers")
    print(f"[INFO] Imported {session_count} sessions")
    print(f"[INFO] Imported {message_count} messages")
    print(f"[OK] Saved to: {output_file}")

    return peer_count + session_count


def main():
    parser = argparse.ArgumentParser(
        description="Import LLM Wiki markdown files into honcho-local memory"
    )
    parser.add_argument(
        '--wiki', '-w',
        default='wiki',
        help='Path to wiki directory',
    )
    parser.add_argument(
        '--output', '-o',
        default='honco_imported-wiki.json',
        help='Output honcho JSON file',
    )
    parser.add_argument(
        '--workspace',
        default='imported-wiki',
        help='Workspace ID for imported data',
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Wiki to Honcho Import")
    print("=" * 60)
    print(f"[1/4] Scanning wiki directory: {args.wiki}")

    try:
        total = import_wiki_to_honcho(
            wiki_path=args.wiki,
            output_file=args.output,
            workspace=args.workspace,
        )

        print(f"[2/4] Parsed {total} entities")
        print(f"[3/4] Built honcho storage structure")
        print(f"[4/4] Saved to: {args.output}")

        print("\n" + "=" * 60)
        print("[SUCCESS] Wiki import complete!")
        print(f"\nNext steps:")
        print(f"  1. Load the storage: get_local_honcho('{args.workspace}')")
        print(f"  2. Query the memory: memory.chat(peer_id, 'What do you know?')")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
