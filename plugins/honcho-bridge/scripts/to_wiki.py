#!/usr/bin/env python3
"""
Honcho to Wiki Export Script

Exports official Honcho memory to LLM Wiki markdown format.
Compatible with Karpathy's LLM Wiki pattern and Obsidian.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from honcho import Honcho as HonchoClient

    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False
    print("[WARNING] honcho-ai not installed. Run: pip install honcho-ai")


def sanitize_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, "_")
    return name


def escape_yaml(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def format_timestamp(ts) -> str:
    if ts is None:
        return ""
    try:
        if hasattr(ts, "strftime"):
            return ts.strftime("%Y-%m-%d %H:%M")
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


def ts_to_iso(ts) -> str:
    if ts is None:
        return ""
    if hasattr(ts, "isoformat"):
        return ts.isoformat()
    return str(ts)


def create_peer_page(
    peer_id: str,
    created_at,
    sessions: List[Dict],
    workspace: str,
    metadata: Optional[Dict] = None,
) -> str:
    session_count = len(sessions)
    session_links = []
    for session in sessions:
        sid = session.get("id", "")
        title = session.get("title", f"Session {sid}")
        session_links.append(f"- [[{sid}]] - {title}")

    meta = metadata or {}
    name = meta.get("name", peer_id)
    peer_type = meta.get("peer_type", "peer")

    content = f"""---
peer_id: {escape_yaml(peer_id)}
name: {escape_yaml(str(name))}
peer_type: {escape_yaml(str(peer_type))}
created_at: {escape_yaml(ts_to_iso(created_at))}
workspace: {escape_yaml(workspace)}
session_count: {session_count}
---

# {name}

**Type:** {peer_type}
**Created:** {format_timestamp(created_at)}
**Sessions:** {session_count}

"""

    if session_links:
        content += "## Sessions\n\n"
        content += "\n".join(session_links)
        content += "\n"

    return content


def create_session_page(
    session_id: str,
    created_at,
    messages: List,
    peer_metadata: Dict,
    workspace: str,
) -> str:
    title = f"Session {session_id}"

    participant_ids = []
    seen = set()
    for msg in messages:
        pid = getattr(msg, "peer_id", None) or msg.get("peer_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            participant_ids.append(pid)

    participants_list = []
    for pid in participant_ids:
        meta = peer_metadata.get(pid, {})
        name = meta.get("name", pid)
        ptype = meta.get("peer_type", "peer")
        participants_list.append(f"- **{name}** ({ptype}) - [[{pid}]]")

    transcript_lines = []
    topics = set()
    for msg in messages:
        if hasattr(msg, "peer_id"):
            peer_id = msg.peer_id
            content_text = msg.content
            msg_created = msg.created_at
        else:
            peer_id = msg.get("peer_id", "")
            content_text = msg.get("content", "")
            msg_created = msg.get("created_at", "")

        meta = peer_metadata.get(peer_id, {})
        peer_name = meta.get("name", peer_id)

        transcript_lines.append(f"### {format_timestamp(msg_created)}\n")
        transcript_lines.append(f"**{peer_name}**:\n")
        transcript_lines.append(f"{content_text}\n")

        for word in content_text.lower().split():
            if len(word) > 5 and word.isalpha():
                topics.add(word.capitalize())

    content = f"""---
session_id: {escape_yaml(session_id)}
title: {escape_yaml(title)}
created_at: {escape_yaml(ts_to_iso(created_at))}
workspace: {escape_yaml(workspace)}
message_count: {len(messages)}
participants: {participant_ids}
---

# {title}

**Created:** {format_timestamp(created_at)}
**Messages:** {len(messages)}

## Participants

{chr(10).join(participants_list) if participants_list else "_None_"}

## Transcript

{chr(10).join(transcript_lines)}
"""

    if topics:
        unique_topics = sorted(list(topics))[:10]
        content += "\n## Topics\n\n"
        for topic in unique_topics:
            content += f"- {topic}\n"

    return content


def create_index(
    peers_data: List[Dict], sessions_data: List[Dict], workspace: str
) -> str:
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_messages = sum(s.get("message_count", 0) for s in sessions_data)

    content = f"""---
title: Honcho Wiki Index
workspace: {escape_yaml(workspace)}
exported_at: {escape_yaml(export_time)}
---

# Honcho Wiki Index

**Workspace:** {workspace}
**Exported:** {export_time}

## Statistics

- **Total Peers:** {len(peers_data)}
- **Total Sessions:** {len(sessions_data)}
- **Total Messages:** {total_messages}

## Peers

"""
    for p in peers_data:
        pid = p.get("id", "")
        name = p.get("name", pid)
        session_count = p.get("session_count", 0)
        content += f"### [[{pid}]]\n\n"
        content += f"**Name:** {name}\n"
        content += f"**Sessions:** {session_count}\n\n"

    content += "## Sessions\n\n"
    for session in honcho.sessions():
        session_id = session.id
        created_at = session.created_at

        all_messages = list(session.messages())

        sessions_data.append(
            {
                "id": session_id,
                "created_at": created_at,
                "message_count": len(all_messages),
                "messages": all_messages,
            }
        )

        participating_peers = set(m.peer_id for m in all_messages)
        for pid in participating_peers:
            peer_session_counts[pid] = peer_session_counts.get(pid, 0) + 1

    print(f"[INFO] Found {len(sessions_data)} sessions")

    for p in peers_data:
        p["session_count"] = peer_session_counts.get(p["id"], 0)

    peer_sessions_map: Dict[str, List[Dict]] = {p["id"]: [] for p in peers_data}
    for s in sessions_data:
        participating = set(
            getattr(msg, "peer_id", None) or msg.get("peer_id", "")
            for msg in s["messages"]
        )
        for pid in participating:
            if pid in peer_sessions_map:
                peer_sessions_map[pid].append(
                    {"id": s["id"], "title": f"Session {s['id']}"}
                )

    print("[INFO] Writing peer pages...")
    for p in peers_data:
        peer_content = create_peer_page(
            peer_id=p["id"],
            created_at=p["created_at"],
            sessions=peer_sessions_map.get(p["id"], []),
            workspace=workspace,
            metadata=p["metadata"],
        )
        peer_file = wiki_path / "peers" / f"{sanitize_filename(p['id'])}.md"
        with open(peer_file, "w", encoding="utf-8") as f:
            f.write(peer_content)

    print("[INFO] Writing session pages...")
    total_messages = 0
    for s in sessions_data:
        session_content = create_session_page(
            session_id=s["id"],
            created_at=s["created_at"],
            messages=s["messages"],
            peer_metadata=peer_metadata,
            workspace=workspace,
        )
        session_file = wiki_path / "sessions" / f"{sanitize_filename(s['id'])}.md"
        with open(session_file, "w", encoding="utf-8") as f:
            f.write(session_content)
        total_messages += s["message_count"]

    print("[INFO] Writing index...")
    index_content = create_index(peers_data, sessions_data, workspace)
    with open(wiki_path / "index.md", "w", encoding="utf-8") as f:
        f.write(index_content)

    stats = {
        "peers": len(peers_data),
        "sessions": len(sessions_data),
        "messages": total_messages,
    }
    append_log(workspace, stats, str(wiki_path))

    file_count = len(peers_data) + len(sessions_data) + 2
    return file_count


def main():
    parser = argparse.ArgumentParser(
        description="Export Honcho memory to LLM Wiki markdown format"
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
        help="Workspace ID",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="wiki",
        help="Output directory for wiki files",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Honcho to Wiki Export")
    print("=" * 60)
    print(f"[1/4] Connecting to Honcho: {args.base_url}")
    print(f"[2/4] Workspace: {args.workspace}")

    try:
        file_count = export_honcho_to_wiki(
            base_url=args.base_url,
            workspace=args.workspace,
            output_dir=args.output,
        )

        print(f"[3/4] Created wiki directory: {args.output}/")
        print(f"[4/4] Generated {file_count} wiki files")

        print("\n" + "=" * 60)
        print("[SUCCESS] Wiki export complete!")
        print(f"\nNext steps:")
        print(f"  1. Open {args.output}/ in Obsidian")
        print(f"  2. Enable graph view to see connections")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
