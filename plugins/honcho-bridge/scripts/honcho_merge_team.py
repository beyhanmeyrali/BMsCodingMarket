#!/usr/bin/env python3
"""
Import team memory markdown into Honcho.

Parses markdown files exported by honcho_export_team.py
and merges them with interactive conflict resolution.
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

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


def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body_content).
    """
    if not content.startswith("---"):
        return None, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content

    frontmatter_text = parts[1]
    body = parts[2].strip()

    # Parse simple YAML
    frontmatter = {}
    for line in frontmatter_text.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, body


def extract_observations(content: str) -> List[str]:
    """
    Extract individual observations from markdown content.

    Looks for list items and paragraphs.
    """
    observations = []

    lines = content.split("\n")
    current_observation = []

    for line in lines:
        line = line.strip()

        # Skip headers and metadata
        if line.startswith("#") or line.startswith("---"):
            continue

        # Check for list items
        if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
            if current_observation:
                observations.append(" ".join(current_observation))
                current_observation = []

            # Extract the list item content
            content = re.sub(r"^[-*•\d+\.\s]*", "", line)
            current_observation.append(content)

        elif line and current_observation:
            # Continuation of current observation
            current_observation.append(line)

    # Add the last observation
    if current_observation:
        observations.append(" ".join(current_observation))

    return observations


def detect_conflicts(existing_obs: List[str], new_obs: List[str]) -> List[Dict]:
    """
    Detect potential conflicts between existing and new observations.

    Returns list of conflict objects.
    """
    conflicts = []

    for new in new_obs:
        new_lower = new.lower()

        for existing in existing_obs:
            existing_lower = existing.lower()

            # Check for contradictions
            if ("never" in new_lower and "always" in existing_lower) or \
               ("always" in new_lower and "never" in existing_lower) or \
               ("avoid" in new_lower and "prefer" in existing_lower) or \
               ("prefer" in new_lower and "avoid" in existing_lower):

                # Check if they talk about similar things
                words_new = set(w for w in new_lower.split() if len(w) > 4)
                words_existing = set(w for w in existing_lower.split() if len(w) > 4)

                if words_new & words_existing:  # Overlap
                    conflicts.append({
                        "new": new,
                        "existing": existing,
                        "type": "contradiction"
                    })

            # Check for duplicates
            if new_lower == existing_lower or \
               (len(new_lower) > 20 and new_lower in existing_lower) or \
               (len(existing_lower) > 20 and existing_lower in new_lower):

                conflicts.append({
                    "new": new,
                    "existing": existing,
                    "type": "duplicate"
                })

    return conflicts


def resolve_conflicts_interactive(conflicts: List[Dict]) -> List[str]:
    """
    Interactive conflict resolution.

    Returns list of observations to keep.
    """
    if not conflicts:
        return []

    print("\n" + "=" * 60)
    print("CONFLICT RESOLUTION")
    print("=" * 60)

    resolved = []

    for i, conflict in enumerate(conflicts, 1):
        print(f"\n## Conflict {i}/{len(conflicts)}")
        print(f"Type: {conflict['type'].upper()}")
        print(f"\nExisting: {conflict['existing'][:100]}...")
        print(f"New:      {conflict['new'][:100]}...")

        while True:
            choice = input("\nChoose: (k)eep existing, (n)ew, (b)oth, (s)kip all ").strip().lower()

            if choice == "k":
                resolved.append(conflict['existing'])
                break
            elif choice == "n":
                resolved.append(conflict['new'])
                break
            elif choice == "b":
                resolved.append(conflict['existing'])
                resolved.append(conflict['new'])
                break
            elif choice == "s":
                return resolved  # Skip remaining
            else:
                print("Invalid choice. Please enter k, n, b, or s.")

    return resolved


def merge_team_memory(
    import_dir: str,
    base_url: str,
    workspace: str,
    peer_id: str,
    interactive: bool = True,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Import and merge team memory from markdown files.

    Returns statistics about the merge.
    """
    if not HONCHO_AVAILABLE:
        print("[ERROR] honcho-ai not installed")
        return {}

    import_path = Path(import_dir)
    if not import_path.exists():
        print(f"[ERROR] Import directory does not exist: {import_dir}")
        return {}

    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    peer = client.peer(peer_id, metadata={"name": "User", "peer_type": "user"})

    stats = {
        "files_read": 0,
        "observations_imported": 0,
        "conflicts_detected": 0,
        "conflicts_resolved": 0,
    }

    # Get existing observations for conflict detection
    existing_response = peer.chat("What are all the observations about this user? List them.")
    existing_obs = extract_observations(existing_response) if existing_response else []

    # Read all markdown files
    md_files = list(import_path.glob("*.md"))

    # Skip index
    md_files = [f for f in md_files if f.name != "index.md"]

    for md_file in md_files:
        print(f"\n[Reading] {md_file.name}")

        try:
            content = md_file.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(content)

            observations = extract_observations(body)

            if not observations:
                print(f"  [Skip] No observations found")
                continue

            stats["files_read"] += 1

            # Detect conflicts
            conflicts = detect_conflicts(existing_obs, observations)

            if conflicts:
                stats["conflicts_detected"] += len(conflicts)
                print(f"  [Warning] {len(conflicts)} conflict(s) detected")

                if interactive and not dry_run:
                    resolved = resolve_conflicts_interactive(conflicts)
                    stats["conflicts_resolved"] += len(resolved)
                    # Use resolved observations instead of originals
                    observations = [o for o in observations if o not in [c['new'] for c in conflicts]]

            # Import observations
            if not dry_run:
                session_id = f"team-import-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                session = client.session(session_id)

                for obs in observations:
                    message_content = f"[TEAM MEMORY] {obs}"
                    msg = peer.message(message_content)
                    session.add_messages([msg])
                    stats["observations_imported"] += 1
            else:
                print(f"  [Dry Run] Would import {len(observations)} observation(s)")
                stats["observations_imported"] += len(observations)

        except Exception as e:
            print(f"  [Error] Failed to process {md_file.name}: {e}")

    return stats


def main():
    """CLI for team memory import."""
    parser = argparse.ArgumentParser(
        description="Import team memory markdown into Honcho"
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
        "--import-dir", "-i",
        required=True,
        help="Directory containing team memory files"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip conflict resolution (auto-keep existing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Honcho Team Memory Import")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print(f"Import dir: {args.import_dir}")
    print(f"Interactive: {not args.non_interactive}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 60)

    try:
        stats = merge_team_memory(
            args.import_dir,
            args.base_url,
            args.workspace,
            args.peer,
            interactive=not args.non_interactive,
            dry_run=args.dry_run
        )

        print("\n" + "=" * 60)
        print("Import Summary")
        print("=" * 60)
        print(f"Files read: {stats.get('files_read', 0)}")
        print(f"Observations imported: {stats.get('observations_imported', 0)}")
        print(f"Conflicts detected: {stats.get('conflicts_detected', 0)}")
        print(f"Conflicts resolved: {stats.get('conflicts_resolved', 0)}")

        if not args.dry_run:
            print("\n[SUCCESS] Team memory imported!")
        else:
            print("\n[DRY RUN] No actual changes made")

    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
