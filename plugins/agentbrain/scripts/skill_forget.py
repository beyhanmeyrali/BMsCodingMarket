"""
/forget skill implementation

Removes memories from both the vector database and file storage.
"""

import os
import sys
from pathlib import Path

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.qdrant import QdrantProvider
from regenerate_index import generate_index, write_index


def get_config() -> dict:
    """Get configuration from environment variables."""
    return {
        "qdrant_host": os.environ.get("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.environ.get("QDRANT_PORT", "6333")),
        "qdrant_collection": os.environ.get("QDRANT_COLLECTION", "agentbrain_memories"),
        "embedding_dim": int(os.environ.get("EMBEDDING_DIMENSION", "1024")),
    }


def get_memory_dir() -> Path:
    """Get the memory directory path."""
    memory_dir = os.environ.get("MEMORY_DIR", "~/.claude/memory")
    if memory_dir == "~/.claude/memory":
        memory_dir = str(Path.home() / ".claude" / "memory")
    return Path(memory_dir).expanduser()


def resolve_memory_name(name: str) -> Path:
    """
    Resolve memory name to full file path.

    Args:
        name: Memory name (with or without .md extension)

    Returns:
        Full path to memory file, or None if not found.
    """
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
        # Remove .md for comparison
        file_stem = file.stem.lower()
        if search_term in file_stem:
            return file

    return None


def skill_forget(name: str) -> str:
    """
    Remove a memory from AgentBrain.

    Args:
        name: Memory name or file name

    Returns:
        Confirmation message.
    """
    if not name or not name.strip():
        return "# Please provide a memory name\n\nUsage: `/forget <memory-name>`"

    # Resolve file path
    file_path = resolve_memory_name(name)

    if not file_path:
        return f"# Memory not found\n\n> Could not find memory matching: \"{name}\"\n\nUse `/recall` to find the exact name."

    # Get memory ID (from filename)
    import hashlib
    memory_id = hashlib.md5(str(file_path).encode("utf-8")).hexdigest()

    # Delete from Qdrant
    try:
        config = get_config()
        qdrant = QdrantProvider(
            host=config["qdrant_host"],
            port=config["qdrant_port"],
            collection=config["qdrant_collection"],
            embedding_dim=config["embedding_dim"],
        )
        qdrant.initialize()

        if qdrant.delete(memory_id):
            deleted_from_db = True
        else:
            deleted_from_db = False
    except Exception as e:
        return f"# Failed to delete from vector database\n\nError: {e}"

    # Delete file
    try:
        file_path.unlink()
        deleted_file = True
    except Exception as e:
        return f"# Failed to delete file\n\nError: {e}"

    # Regenerate index
    try:
        index_content, count = generate_index()
        write_index(index_content)
    except Exception:
        pass  # Non-fatal

    status = []
    if deleted_from_db:
        status.append("- Deleted from vector database")
    if deleted_file:
        status.append(f"- Deleted file: `{file_path.name}`")

    return f"""# Forgot: {file_path.name}

{chr(10).join(status)}

Memory index regenerated.
"""


def main():
    """CLI entry point for testing."""
    if len(sys.argv) < 2:
        print("Usage: python skill_forget.py <memory-name>")
        return 1

    name = sys.argv[1]
    result = skill_forget(name)
    print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
