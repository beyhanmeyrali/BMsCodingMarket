#!/usr/bin/env python3
"""
Export Honcho memory as team-shareable markdown.

Creates PR-ready markdown files that can be shared with a team
and later merged with honcho_merge_team.py.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

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


def escape_yaml(value: str) -> str:
    """Escape string for YAML."""
    if not isinstance(value, str):
        return str(value)
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def export_for_pr(
    base_url: str,
    workspace: str,
    peer_id: str,
    output_dir: str
) -> int:
    """
    Export observations as PR-ready markdown.

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

    peer = client.peer(peer_id)

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Query for all observations
    print(f"[Honcho] Querying observations for peer: {peer_id}")

    response = peer.chat(
        "Provide a comprehensive summary of all observations about this user. "
        "Include preferences, rules, decisions, and any other learned information. "
        "Format with clear sections."
    )

    if not response or "don't have any information" in response.lower():
        print("[Honcho] No observations to export")
        return 0

    # Parse response into sections
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

    # Write each section as a separate file for easier PR review
    count = 0
    index_entries = []

    for section_name, section_lines in sections.items():
        if not section_lines:
            continue

        # Create filename
        safe_name = section_name.replace(" ", "-").replace("/", "-")
        filename = f"{safe_name}.md"
        file_path = out_path / filename

        # Build markdown content with merge metadata
        content_lines = [
            "---",
            f"workspace: {escape_yaml(workspace)}",
            f"peer_id: {escape_yaml(peer_id)}",
            f"exported_at: {escape_yaml(datetime.now().isoformat())}",
            f"section: {escape_yaml(section_name)}",
            "---",
            "",
            f"# {section_name.replace('-', ' ').title()}",
            "",
            "## Observations",
            "",
            *section_lines,
            "",
            "---",
            "",
            "*This file was exported from Honcho memory. "
            f"To merge, use `honcho_merge_team`.*"
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))

        count += 1
        index_entries.append(f"- [{section_name}]({filename})")

    # Write index
    index_path = out_path / "index.md"
    index_content = [
        f"# Team Memory Export",
        "",
        f"**Workspace:** {workspace}",
        f"**Peer:** {peer_id}",
        f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Sections",
        "",
        *index_entries,
        "",
        "---",
        "",
        "## How to Merge",
        "",
        "1. Review the exported markdown files",
        "2. Edit or add observations as needed",
        "3. Run `python honcho_merge_team.py --import-dir {output_dir}`",
    ]

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_content))

    return count + 1  # Include index


def main():
    """CLI for team memory export."""
    parser = argparse.ArgumentParser(
        description="Export Honcho memory for team sharing"
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
        "--output", "-o",
        default="team-memory",
        help="Output directory"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Honcho Team Memory Export")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print(f"Output: {args.output}/")
    print("-" * 60)

    try:
        count = export_for_pr(
            args.base_url,
            args.workspace,
            args.peer,
            args.output
        )

        print("\n" + "=" * 60)
        print(f"[SUCCESS] Exported {count} file(s)")
        print(f"\nNext steps:")
        print(f"  1. Review: {args.output}/")
        print(f"  2. Make any edits")
        print(f"  3. Share with team")
        print(f"  4. Merge with: honcho_merge_team --import-dir {args.output}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
