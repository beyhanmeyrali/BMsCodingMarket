#!/usr/bin/env python3
"""
Wiki to Honcho Import Script

Imports LLM Wiki markdown files into official Honcho memory.
Compatible with Karpathy's LLM Wiki pattern and Obsidian exports.
"""

import sys
import re
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from honcho import Honcho as HonchoClient

    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False
    print("[WARNING] honcho-ai not installed. Run: pip install honcho-ai")


def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError as e:
            print(f"[WARNING] Failed to parse YAML: {e}")
            return None, content
    return None, content


def extract_messages_from_transcript(
    body: str, name_to_peer_id: Dict[str, str]
) -> List[Dict]:
    messages = []
    in_transcript = False
    current_peer_id = None
    pending_content_lines: List[str] = []

    def flush():
        if current_peer_id and pending_content_lines:
            content = " ".join(l for l in pending_content_lines if l)
            if content:
                messages.append({"peer_id": current_peer_id, "content": content})

    for line in body.split("\n"):
        line_stripped = line.strip()

        if line_stripped == "## Transcript":
            in_transcript = True
            continue

        if not in_transcript:
            continue

        if line_stripped.startswith("## "):
            flush()
            current_peer_id = None
            pending_content_lines = []
            in_transcript = False
            continue

        if line_stripped.startswith("### "):
            flush()
            current_peer_id = None
            pending_content_lines = []
            continue

        header = re.match(r"\*\*([^*]+)\*\*(?:\s*\([^)]*\))?:\s*(.*)", line_stripped)
        if header:
            flush()
            name = header.group(1).strip()
            current_peer_id = name_to_peer_id.get(name, name)
            inline = header.group(2).strip()
            pending_content_lines = [inline] if inline else []
            continue

        if current_peer_id is not None:
            pending_content_lines.append(line_stripped)

    flush()
    return messages


def import_peer_page(file_path: Path, honcho) -> Optional[Tuple[str, str]]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        print(f"[WARNING] No frontmatter in {file_path.name}, skipping")
        return None

    peer_id = frontmatter.get("peer_id", file_path.stem)
    name = frontmatter.get("name", peer_id)
    peer_type = frontmatter.get("peer_type", "peer")

    try:
        peer = honcho.peer(
            str(peer_id), metadata={"name": str(name), "peer_type": str(peer_type)}
        )
        print(f"[INFO] Imported peer: {peer_id} ({name})")
        return str(peer_id), str(name)
    except Exception as e:
        print(f"[WARNING] Failed to import peer {peer_id}: {e}")
        return None


def import_session_page(
    file_path: Path,
    honcho,
    name_to_peer_id: Dict[str, str],
    peer_id_to_name: Dict[str, str],
) -> Optional[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        print(f"[WARNING] No frontmatter in {file_path.name}, skipping")
        return None

    session_id = frontmatter.get("session_id", file_path.stem)
    messages = extract_messages_from_transcript(body, name_to_peer_id)

    if not messages:
        print(f"[WARNING] No messages found in {file_path.name}, skipping")
        return None

    try:
        session = honcho.session(str(session_id))

        message_params = []
        for msg in messages:
            peer_id = msg["peer_id"]
            peer = honcho.peer(peer_id)
            message_params.append(peer.message(msg["content"]))

        session.add_messages(message_params)

        print(f"[INFO] Imported session: {session_id} with {len(messages)} messages")
        return str(session_id)
    except Exception as e:
        print(f"[WARNING] Failed to import session {session_id}: {e}")
        return None


def import_wiki_to_honcho(
    wiki_path: str,
    base_url: str,
    workspace: str,
) -> int:
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed. Run: pip install honcho-ai")
        return 0

    wiki_dir = Path(wiki_path)

    if not wiki_dir.exists():
        print(f"[ERROR] Wiki directory not found: {wiki_path}")
        return 0

    peer_files = sorted(wiki_dir.glob("peers/*.md"))
    session_files = sorted(wiki_dir.glob("sessions/*.md"))

    print(f"[INFO] Found {len(peer_files)} peer files")
    print(f"[INFO] Found {len(session_files)} session files")

    honcho = HonchoClient(base_url=base_url, workspace_id=workspace)

    peer_count = 0
    name_to_peer_id: Dict[str, str] = {}
    peer_id_to_name: Dict[str, str] = {}

    for peer_file in peer_files:
        result = import_peer_page(peer_file, honcho)
        if result:
            peer_id, name = result
            name_to_peer_id[name] = peer_id
            name_to_peer_id[peer_id] = peer_id
            peer_id_to_name[peer_id] = name
            peer_count += 1

    session_count = 0
    for session_file in session_files:
        session_id = import_session_page(
            session_file, honcho, name_to_peer_id, peer_id_to_name
        )
        if session_id:
            session_count += 1

    print(f"[INFO] Imported {peer_count} peers")
    print(f"[INFO] Imported {session_count} sessions")

    return peer_count + session_count


def main():
    parser = argparse.ArgumentParser(
        description="Import wiki markdown files into Honcho memory"
    )
    parser.add_argument(
        "--wiki",
        "-w",
        default="wiki",
        help="Path to wiki directory",
    )
    parser.add_argument(
        "--base-url",
        "-b",
        default="http://localhost:8000",
        help="Honcho server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Workspace ID for imported data",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Wiki to Honcho Import")
    print("=" * 60)
    print(f"[1/4] Scanning wiki directory: {args.wiki}")

    try:
        total = import_wiki_to_honcho(
            wiki_path=args.wiki,
            base_url=args.base_url,
            workspace=args.workspace,
        )

        print(f"[2/4] Parsed {total} entities")
        print(f"[3/4] Sent to Honcho server")
        print(f"[4/4] Import complete")

        print("\n" + "=" * 60)
        print("[SUCCESS] Wiki import complete!")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
