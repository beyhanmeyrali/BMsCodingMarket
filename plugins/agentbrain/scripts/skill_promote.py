"""
/promote skill implementation

Promotes memories to wider scopes (team/project/org) for sharing.
"""

import os
import sys
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from upsert import upsert_memory, get_memory_dir
from regenerate_index import generate_index, write_index


def parse_args(args: list) -> tuple[str, str]:
    """
    Parse promotion arguments.

    Args:
        args: Command line arguments

    Returns:
        Tuple of (memory_name, target_scope)
    """
    memory_name = None
    target_scope = None

    for i, arg in enumerate(args):
        if arg == "--to" and i + 1 < len(args):
            target_scope = args[i + 1]
        elif not arg.startswith("--"):
            memory_name = arg

    return memory_name, target_scope


def resolve_memory_name(name: str) -> Path:
    """Resolve memory name to full file path."""
    memory_dir = get_memory_dir()

    # Store original search term
    search_term = name.lower()

    # Add .md if not present
    if not name.endswith(".md"):
        name = f"{name}.md"

    # Direct path
    direct_path = memory_dir / name
    if direct_path.exists():
        return direct_path

    # Try partial match (search term without .md in filename)
    for file in memory_dir.glob("*.md"):
        file_stem = file.stem.lower()
        if search_term in file_stem:
            return file

    return None


def get_current_scope(file_path: Path) -> str:
    """Read the current scope from a memory file."""
    import yaml

    try:
        content = file_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if match:
            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter.get("scope", "user:unknown")
    except Exception:
        pass

    return "user:unknown"


def update_scope(file_path: Path, new_scope: str) -> bool:
    """Update the scope in a memory file."""
    import yaml

    try:
        content = file_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---(.*)", content, re.DOTALL)

        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)

            # Update scope and timestamp
            frontmatter["scope"] = new_scope
            frontmatter["updated_at"] = datetime.now().isoformat()

            # Rebuild file
            new_content = "---\n"
            for key, value in frontmatter.items():
                if isinstance(value, str):
                    new_content += f'{key}: "{value}"\n'
                else:
                    new_content += f"{key}: {value}\n"
            new_content += f"---\n{body}"

            file_path.write_text(new_content, encoding="utf-8")
            return True
    except Exception:
        pass

    return False


def skill_promote(memory_name: str, target_scope: str) -> str:
    """
    Promote a memory to a wider scope.

    Args:
        memory_name: Name of the memory to promote
        target_scope: Target scope (team:X, project:X, org:X)

    Returns:
        Confirmation message.
    """
    if not memory_name:
        return "# Please provide a memory name\n\nUsage: `/promote <memory-name> --to <scope>`"

    if not target_scope:
        return "# Please provide a target scope\n\nUsage: `/promote <memory-name> --to <scope>`\n\nScopes: team:{name}, project:{name}, org:{name}"

    # Validate target scope format
    if not re.match(r"^(team|project|org):", target_scope):
        return f"# Invalid scope format\n\n> Scope must be: team:X, project:X, or org:X\n\nGot: `{target_scope}`"

    # Resolve memory file
    file_path = resolve_memory_name(memory_name)

    if not file_path:
        return f"# Memory not found\n\n> Could not find memory matching: \"{memory_name}\""

    # Get current scope
    current_scope = get_current_scope(file_path)

    # Update scope in file
    if not update_scope(file_path, target_scope):
        return f"# Failed to update memory\n\n> Could not update scope in file: `{file_path.name}`"

    # Re-upsert to Qdrant with new scope
    try:
        memory_id = upsert_memory(str(file_path))
    except Exception as e:
        return f"# Failed to update vector database\n\nError: {e}"

    # Regenerate index
    try:
        index_content, count = generate_index()
        write_index(index_content)
    except Exception:
        pass  # Non-fatal

    # Calculate who can see it now
    scope_type, scope_name = target_scope.split(":", 1)

    if scope_type == "team":
        audience = f"members of the '{scope_name}' team"
    elif scope_type == "project":
        audience = f"anyone working on the '{scope_name}' project"
    elif scope_type == "org":
        audience = f"everyone in the '{scope_name}' organization"
    else:
        audience = f"users with scope: {target_scope}"

    return f"""# Promoted: {file_path.name}

**From:** `{current_scope}`
**To:** `{target_scope}`
**ID:** {memory_id[:8]}...

This memory is now visible to {audience}.
Memory index regenerated.
"""


def main():
    """CLI entry point for testing."""
    if len(sys.argv) < 4:
        print("Usage: python skill_promote.py <memory-name> --to <scope>")
        return 1

    memory_name, target_scope = parse_args(sys.argv[1:])
    result = skill_promote(memory_name, target_scope)
    print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
