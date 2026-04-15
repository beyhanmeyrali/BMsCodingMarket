"""
/remember skill implementation

Stores information to memory with automatic type classification and scoping.
"""

import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from upsert import upsert_memory, get_memory_dir
from regenerate_index import regenerate_index, write_index


def classify_memory(text: str) -> tuple[str, str]:
    """
    Classify memory by type and scope based on content.

    Args:
        text: Memory text

    Returns:
        Tuple of (type, scope)
    """
    text_lower = text.lower()

    # Detect type
    if re.search(r"\bi\s+prefer\b|\bi\s+like\b|\bi\s+use\b|\bi\s+always\b", text_lower):
        memory_type = "user"
    elif re.search(r"\bwe\s+use\b|\bwe\s+chose\b|\bdecision\b|\barchitecture\b", text_lower):
        memory_type = "project"
    elif re.search(r"\bshould\b|\bmust\b|\bdon't\b|\bnever\b|\bconvention\b", text_lower):
        memory_type = "feedback"
    else:
        memory_type = "user"  # Default to user

    # Determine scope
    user_id = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    repo_name = "default"

    # Try to get repo name for project scope
    if memory_type == "project":
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                repo_name = Path(result.stdout.strip()).name
        except Exception:
            pass

        scope = f"project:{repo_name}"
    else:
        scope = f"user:{user_id}"

    return memory_type, scope


def generate_memory_name(text: str, memory_type: str) -> str:
    """
    Generate a filename for the memory.

    Args:
        text: Memory text
        memory_type: Memory type

    Returns:
        Filename (without extension)
    """
    # Extract key phrase
    words = text.lower().split()

    # Get first 3-4 meaningful words
    key_words = []
    for word in words[:10]:
        if len(word) > 3 and word not in {"that", "this", "with", "from", "when"}:
            key_words.append(word)
            if len(key_words) >= 4:
                break

    if not key_words:
        key_words = ["memory"]

    # Create slug
    slug = "_".join(key_words)[:30]

    # Add type prefix and timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{memory_type}_{slug}_{timestamp}"


def skill_remember(text: str) -> str:
    """
    Store information to memory.

    Args:
        text: Information to remember

    Returns:
        Confirmation message.
    """
    if not text or not text.strip():
        return "# Please provide information to remember\n\nUsage: `/remember \"information to store\"`"

    # Classify memory
    memory_type, scope = classify_memory(text)

    # Generate filename
    name = generate_memory_name(text, memory_type)

    # Build frontmatter
    frontmatter = {
        "name": name.replace("_", " ").title(),
        "description": text[:100] + "..." if len(text) > 100 else text,
        "type": memory_type,
        "scope": scope,
        "source": "manual",
        "created_at": datetime.now().isoformat(),
    }

    # Build content
    content = f"# {frontmatter['name']}\n\n{text}\n"

    # Create temporary file for upsert
    memory_dir = get_memory_dir()
    memory_dir.mkdir(parents=True, exist_ok=True)

    temp_file = memory_dir / f"{name}.md"

    # Write file with frontmatter
    file_content = f"---\n"
    for key, value in frontmatter.items():
        if isinstance(value, str):
            file_content += f'{key}: "{value}"\n'
        else:
            file_content += f"{key}: {value}\n"
    file_content += f"---\n\n{content}"

    temp_file.write_text(file_content, encoding="utf-8")

    # Upsert to Qdrant
    try:
        memory_id = upsert_memory(str(temp_file))
    except Exception as e:
        return f"# Failed to store memory\n\nError: {e}"

    # Regenerate index
    try:
        index_content, count = regenerate_index()
        write_index(index_content)
    except Exception:
        pass  # Non-fatal

    return f"""# Memory Stored

**File:** `{name}.md`
**Type:** {memory_type}
**Scope:** {scope}
**ID:** {memory_id[:8]}...

**Content:**
> {text}

This memory will be automatically retrieved in future sessions when relevant.
"""


def main():
    """CLI entry point for testing."""
    if len(sys.argv) < 2:
        print("Usage: python skill_remember.py \"information to remember\"")
        return 1

    text = " ".join(sys.argv[1:])
    result = skill_remember(text)
    print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
