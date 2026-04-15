"""
AgentBrain SubagentStop Hook

Processes the output from the memory-curator subagent.
Writes new memories, updates existing ones, and syncs to Qdrant.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from upsert import upsert_memory, get_memory_dir
from regenerate_index import generate_index, write_index


def get_curator_output_file() -> Path:
    """
    Get the path to the curator output file.

    Returns:
        Path to curator output JSON file.
    """
    curator_dir = plugin_root / ".agentbrain"
    return curator_dir / "curator_output.json"


def has_curator_output() -> bool:
    """
    Check if the curator has produced output.

    Returns:
        True if curator output exists, False otherwise.
    """
    output_file = get_curator_output_file()
    return output_file.exists()


def load_curator_output() -> dict:
    """
    Load the curator output JSON.

    Returns:
        Parsed curator output or empty dict if invalid.
    """
    output_file = get_curator_output_file()

    try:
        content = output_file.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception as e:
        print(f"[AgentBrain] Failed to load curator output: {e}", file=sys.stderr)
        return {}


def process_create_action(memory_data: dict) -> bool:
    """
    Process a 'create' action - write a new memory file.

    Args:
        memory_data: Memory data from curator output

    Returns:
        True if successful, False otherwise.
    """
    memory_dir = get_memory_dir()
    memory_dir.mkdir(parents=True, exist_ok=True)

    file_name = memory_data.get("file", "new_memory.md")
    file_path = memory_dir / file_name

    # Build frontmatter
    frontmatter = memory_data.get("frontmatter", {})
    frontmatter.setdefault("created_at", datetime.now().isoformat())
    frontmatter.setdefault("updated_at", datetime.now().isoformat())
    frontmatter.setdefault("scope", memory_data.get("scope", "user:default"))

    # Build content with frontmatter
    content = f"---\n"
    for key, value in frontmatter.items():
        if isinstance(value, str):
            content += f'{key}: "{value}"\n'
        else:
            content += f"{key}: {value}\n"
    content += f"---\n\n"
    content += memory_data.get("content", "")

    # Write file
    try:
        file_path.write_text(content, encoding="utf-8")
        print(f"[AgentBrain] Created memory: {file_name}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[AgentBrain] Failed to create memory: {e}", file=sys.stderr)
        return False


def process_update_action(memory_data: dict) -> bool:
    """
    Process an 'update' action - update an existing memory file.

    Args:
        memory_data: Memory data from curator output

    Returns:
        True if successful, False otherwise.
    """
    memory_dir = get_memory_dir()
    file_name = memory_data.get("file")
    file_path = memory_dir / file_name

    if not file_path.exists():
        print(f"[AgentBrain] Memory file not found for update: {file_name}", file=sys.stderr)
        # Fall back to create
        return process_create_action(memory_data)

    try:
        # Read existing content
        existing_content = file_path.read_text(encoding="utf-8")

        # Append update section
        update_content = memory_data.get("content", "")
        updated_content = existing_content + f"\n\n## Updated {datetime.now().strftime('%Y-%m-%d')}\n\n{update_content}"

        file_path.write_text(updated_content, encoding="utf-8")
        print(f"[AgentBrain] Updated memory: {file_name}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[AgentBrain] Failed to update memory: {e}", file=sys.stderr)
        return False


def process_skip_action(memory_data: dict) -> bool:
    """
    Process a 'skip' action - log why memory was skipped.

    Args:
        memory_data: Memory data from curator output

    Returns:
        True (skip is always successful).
    """
    reason = memory_data.get("reason", "Duplicate")
    file_name = memory_data.get("file", "unknown")
    print(f"[AgentBrain] Skipped {file_name}: {reason}", file=sys.stderr)
    return True


def process_curator_memories(curator_output: dict) -> dict:
    """
    Process all memories from curator output.

    Args:
        curator_output: Parsed curator JSON output

    Returns:
        Summary of actions taken.
    """
    memories = curator_output.get("memories", [])

    summary = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "files": [],
    }

    for memory_data in memories:
        action = memory_data.get("action", "skip")
        file_name = memory_data.get("file", "unknown")

        try:
            if action == "create":
                if process_create_action(memory_data):
                    summary["created"] += 1
                    summary["files"].append(file_name)
                else:
                    summary["failed"] += 1

            elif action == "update":
                if process_update_action(memory_data):
                    summary["updated"] += 1
                    summary["files"].append(file_name)
                else:
                    summary["failed"] += 1

            elif action == "skip":
                process_skip_action(memory_data)
                summary["skipped"] += 1

        except Exception as e:
            print(f"[AgentBrain] Error processing {file_name}: {e}", file=sys.stderr)
            summary["failed"] += 1

    return summary


def sync_to_qdrant(summary: dict) -> None:
    """
    Sync new/updated memories to Qdrant.

    Args:
        summary: Summary of actions taken.
    """
    if not summary["files"]:
        return

    print(f"[AgentBrain] Syncing {len(summary['files'])} memories to Qdrant...", file=sys.stderr)

    for file_name in summary["files"]:
        try:
            # Use relative path for upsert
            upsert_memory(file_name)
        except Exception as e:
            print(f"[AgentBrain] Failed to sync {file_name}: {e}", file=sys.stderr)


def cleanup_curator_files() -> None:
    """Clean up temporary curator files."""
    curator_dir = plugin_root / ".agentbrain"

    files_to_clean = [
        curator_dir / "curator_prompt.txt",
        curator_dir / "curator_output.json",
        curator_dir / "curation_needed.txt",
    ]

    for file_path in files_to_clean:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass


def main():
    """Main entry point for SubagentStop hook."""

    # Check if this is a curator subagent finishing
    if os.environ.get("AGENTBRAIN_CURATOR_SUBAGENT", "").lower() != "true":
        return

    # Check if we have curator output to process
    if not has_curator_output():
        print("[AgentBrain] No curator output to process", file=sys.stderr)
        return

    # Load and process curator output
    curator_output = load_curator_output()
    if not curator_output:
        return

    summary = process_curator_memories(curator_output)

    # Log summary
    print(f"[AgentBrain] Curation complete: "
          f"{summary['created']} created, "
          f"{summary['updated']} updated, "
          f"{summary['skipped']} skipped", file=sys.stderr)

    # Sync to Qdrant if we have new/updated memories
    if summary["created"] + summary["updated"] > 0:
        sync_to_qdrant(summary)

        # Regenerate memory index
        try:
            generate_index()
            write_index(index_content)
        except Exception as e:
            print(f"[AgentBrain] Failed to regenerate index: {e}", file=sys.stderr)

    # Clean up temporary files
    cleanup_curator_files()


if __name__ == "__main__":
    main()
