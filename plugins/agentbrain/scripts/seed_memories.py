"""
Seed Memories Script

Import existing memory files into the vector database.
One-time script to bootstrap AgentBrain with existing memories.
"""

import os
import sys
import time
from pathlib import Path
from typing import List

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from upsert import upsert_memory, get_memory_dir


def discover_memory_files() -> List[Path]:
    """
    Discover all memory files in the memory directory.

    Returns:
        List of memory file paths.
    """
    memory_dir = get_memory_dir()

    if not memory_dir.exists():
        print(f"Memory directory not found: {memory_dir}")
        return []

    files = []
    for md_file in memory_dir.glob("*.md"):
        # Skip the index itself
        if md_file.name == "MEMORY.md":
            continue
        files.append(md_file)

    return sorted(files)


def seed_all_memories(skip_errors: bool = True) -> dict:
    """
    Seed all memory files into the vector database.

    Args:
        skip_errors: Continue on error if True

    Returns:
        Dict with success count, error count, and errors list.
    """
    files = discover_memory_files()

    if not files:
        return {"success": 0, "errors": 0, "error_list": []}

    results = {
        "success": 0,
        "errors": 0,
        "error_list": [],
    }

    print(f"Found {len(files)} memory files to seed...")

    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing {file_path.name}...", end=" ")

        try:
            memory_id = upsert_memory(str(file_path))
            print(f"OK ({memory_id[:8]}...)")
            results["success"] += 1

        except Exception as e:
            print(f"ERROR: {e}")
            results["errors"] += 1
            results["error_list"].append((str(file_path), str(e)))

            if not skip_errors:
                print("\nStopping due to error. Use --skip-errors to continue.")
                break

    return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed existing memories into AgentBrain")
    parser.add_argument("--skip-errors", action="store_true", default=True,
                        help="Continue on errors (default: True)")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Stop on first error")

    args = parser.parse_args()

    # Override if fail-fast is set
    skip_errors = not args.fail_fast

    print("AgentBrain Memory Seeding")
    print("=" * 40)
    print()

    results = seed_all_memories(skip_errors=skip_errors)

    print()
    print("=" * 40)
    print("Seeding complete!")
    print(f"  Success: {results['success']}")
    print(f"  Errors:  {results['errors']}")

    if results["error_list"]:
        print("\nErrors:")
        for file_path, error in results["error_list"]:
            print(f"  - {file_path}: {error}")

    return 0 if results["errors"] == 0 or skip_errors else 1


if __name__ == "__main__":
    sys.exit(main())
