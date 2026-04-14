#!/usr/bin/env python3
"""
Bidirectional sync between Honcho and Claude's native memory system.

Claude Code has a built-in memory system at $HOME/.claude/memory/ that stores
information about users in markdown files with frontmatter. This script syncs
that data with Honcho for unified memory management.
"""

import os
import sys
import argparse
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

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


# Claude memory types
MEMORY_TYPES = {
    "user": "User profile and role information",
    "feedback": "User feedback and behavioral guidance",
    "project": "Project-specific context and decisions",
    "reference": "Pointers to external resources",
}


def get_claude_memory_dir() -> Path:
    """Get the Claude Code memory directory."""
    return Path.home() / ".claude" / "memory"


def parse_memory_file(file_path: Path) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Parse a Claude memory file.

    Returns:
        Tuple of (frontmatter_dict, content_body)
    """
    if not file_path.exists():
        return None, None

    content = file_path.read_text(encoding="utf-8")

    # Parse frontmatter (YAML between --- delimiters)
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1]
            body = parts[2].strip()

            # Parse simple YAML frontmatter
            for line in frontmatter_text.split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

    return frontmatter, body


def classify_observation(content: str, frontmatter: Dict) -> str:
    """
    Classify an observation into Claude memory types.

    Returns: user, feedback, project, or reference
    """
    mem_type = frontmatter.get("type", "")

    if mem_type in MEMORY_TYPES:
        return mem_type

    # Try to classify from content
    content_lower = content.lower()

    # Check for feedback patterns (rules, preferences)
    if any(word in content_lower for word in ["rule:", "why:", "how to apply:", "preference", "avoid"]):
        return "feedback"

    # Check for project patterns
    if any(word in content_lower for word in ["project", "workspace", "decision", "implementation"]):
        return "project"

    # Check for reference patterns
    if any(word in content_lower for word in ["link:", "url:", "https://", "http://", "reference"]):
        return "reference"

    # Check for user patterns
    if any(word in content_lower for word in ["user is", "user prefers", "user works", "role:", "goal:"]):
        return "user"

    # Default to feedback (most common)
    return "feedback"


def write_memory_file(memory_dir: Path, mem_type: str, name: str, content: str, frontmatter: Optional[Dict] = None) -> Path:
    """
    Write a memory file to Claude's memory directory.

    Returns the path to the written file.
    """
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from name
    safe_name = re.sub(r'[^\w\s-]', '', name).strip()
    safe_name = re.sub(r'[-\s]+', '-', safe_name)
    filename = f"{mem_type}_{safe_name.lower()}.md"
    file_path = memory_dir / filename

    # Build frontmatter
    if frontmatter is None:
        frontmatter = {}

    frontmatter.setdefault("name", name)
    frontmatter.setdefault("type", mem_type)
    frontmatter.setdefault("description", f"Synced from Honcho at {datetime.now().isoformat()}")

    # Write file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        for key, value in frontmatter.items():
            f.write(f"{key}: {value}\n")
        f.write("---\n\n")
        f.write(content)

    return file_path


def honcho_to_claude(workspace: str, peer_id: str, base_url: str) -> int:
    """
    Export Honcho observations to Claude memory files.

    Returns count of files created.
    """
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed")
        return 0

    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    memory_dir = get_claude_memory_dir()
    memory_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Honcho] Querying observations for peer: {peer_id}")

    try:
        peer = client.peer(peer_id)

        # Query for all observations about the user
        # We use chat to get a comprehensive summary
        response = peer.chat(
            "Provide a comprehensive summary of all observations about this user. "
            "Include preferences, rules, decisions, and any other learned information. "
            "Format with clear sections for different types of information."
        )

        if not response or "don't have any information" in response.lower():
            print("[Honcho] No observations found to sync")
            return 0

        # Parse the response into sections
        sections = {}
        current_section = "general"
        sections[current_section] = []

        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            if line.startswith("#") or line.endswith(":"):
                section_name = line.strip("#").strip().strip(":").lower()
                if section_name:
                    current_section = section_name
                    sections[current_section] = []

            sections[current_section].append(line)

        # Write each section as a memory file
        count = 0
        for section_name, section_lines in sections.items():
            if not section_lines:
                continue

            content = "\n".join(section_lines)

            # Classify the memory type
            mem_type = classify_observation(content, {"type": section_name})

            # Generate a name for the memory
            name = f"honcho_{section_name}"

            # Write the memory file
            try:
                write_memory_file(memory_dir, mem_type, name, content)
                count += 1
                print(f"  [Wrote] {mem_type}_{name}.md")
            except Exception as e:
                print(f"  [Error] Failed to write {name}: {e}")

        print(f"[Honcho] Synced {count} observation(s) to Claude memory")
        return count

    except Exception as e:
        print(f"[ERROR] Honcho to Claude sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 0


def claude_to_honcho(workspace: str, peer_id: str, base_url: str) -> int:
    """
    Import Claude memory files into Honcho.

    Returns count of messages stored.
    """
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed")
        return 0

    memory_dir = get_claude_memory_dir()

    if not memory_dir.exists():
        print("[Honcho] Claude memory directory does not exist")
        return 0

    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})

    # Use a special session for imported memories
    session_id = "claude-memory-import"
    session = client.session(session_id)

    count = 0

    for mem_file in memory_dir.glob("*.md"):
        try:
            frontmatter, content = parse_memory_file(mem_file)

            if not content:
                continue

            # Create a message with context
            mem_type = frontmatter.get("type", "unknown") if frontmatter else "unknown"
            name = frontmatter.get("name", mem_file.stem) if frontmatter else mem_file.stem

            message_content = (
                f"[CLAUDE MEMORY] Type: {mem_type}\n"
                f"Name: {name}\n"
                f"Source: Claude native memory\n\n"
                f"{content}"
            )

            msg = peer.message(message_content)
            session.add_messages([msg])

            count += 1
            print(f"  [Imported] {mem_file.name}")

        except Exception as e:
            print(f"  [Error] Failed to import {mem_file.name}: {e}")

    print(f"[Honcho] Imported {count} memory file(s) from Claude")
    return count


def sync_bidirectional(workspace: str, peer_id: str, base_url: str) -> Dict[str, int]:
    """Perform bidirectional sync between Honcho and Claude memory."""
    print("[Honcho] Starting bidirectional sync...")

    results = {
        "honcho_to_claude": 0,
        "claude_to_honcho": 0,
    }

    # First, export from Honcho to Claude
    print("\n[1/2] Honcho → Claude")
    results["honcho_to_claude"] = honcho_to_claude(workspace, peer_id, base_url)

    # Then, import from Claude to Honcho
    print("\n[2/2] Claude → Honcho")
    results["claude_to_honcho"] = claude_to_honcho(workspace, peer_id, base_url)

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync between Honcho and Claude's native memory system"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["honcho-to-claude", "claude-to-honcho", "bidirectional"],
        default=os.getenv("HONCHO_CLAUDE_SYNC_MODE", "bidirectional"),
        help="Sync direction (default: from env or bidirectional)"
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without actually syncing"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Honcho-Claude Memory Sync")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print(f"Claude Memory: {get_claude_memory_dir()}")
    print("-" * 60)

    if args.dry_run:
        print("[DRY RUN] No actual changes will be made")
        # Could add more dry-run logic here
        return

    try:
        if args.mode == "honcho-to-claude":
            count = honcho_to_claude(args.workspace, args.peer, args.base_url)
            print(f"\n[SUCCESS] Synced {count} file(s) to Claude memory")

        elif args.mode == "claude-to-honcho":
            count = claude_to_honcho(args.workspace, args.peer, args.base_url)
            print(f"\n[SUCCESS] Imported {count} file(s) to Honcho")

        else:  # bidirectional
            results = sync_bidirectional(args.workspace, args.peer, args.base_url)
            print("\n" + "=" * 60)
            print("[SUCCESS] Bidirectional sync complete!")
            print(f"  Honcho → Claude: {results['honcho_to_claude']} file(s)")
            print(f"  Claude → Honcho: {results['claude_to_honcho']} file(s)")
            print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
