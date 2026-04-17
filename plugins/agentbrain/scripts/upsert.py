"""
Upsert Script

Writes or updates memories in the vector database.
Handles new memories and updates to existing ones.
"""

import os
import sys
import time
import hashlib
from pathlib import Path

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.ollama import OllamaEmbedder, OllamaEmbedError
from providers.qdrant import QdrantProvider
from providers.base import Memory, TrustMetadata


def get_config() -> dict:
    """Get configuration from environment variables."""
    return {
        # Qdrant config
        "qdrant_host": os.environ.get("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.environ.get("QDRANT_PORT", "6333")),
        "qdrant_collection": os.environ.get("QDRANT_COLLECTION", "agentbrain_memories"),
        "qdrant_api_key": os.environ.get("QDRANT_API_KEY", ""),
        # Ollama config
        "ollama_base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "embedding_model": os.environ.get("EMBEDDING_MODEL", "qwen3-embedding:0.6b"),
        "embedding_dim": int(os.environ.get("EMBEDDING_DIMENSION", "1024")),
        # Default scope
        "default_scope": os.environ.get("AGENTBRAIN_SCOPE", "user"),
    }


def get_memory_dir() -> Path:
    """Get the memory directory path."""
    memory_dir = os.environ.get("MEMORY_DIR", "~/.claude/memory")
    if memory_dir == "~/.claude/memory":
        memory_dir = str(Path.home() / ".claude" / "memory")
    return Path(memory_dir).expanduser()


def load_memory_file(file_path: str) -> dict:
    """
    Load a memory file and extract metadata.

    Args:
        file_path: Path to memory file (relative or absolute)

    Returns:
        Dict with content, frontmatter, and metadata.
    """
    memory_dir = get_memory_dir()

    # Handle relative paths
    if not Path(file_path).is_absolute():
        full_path = memory_dir / file_path
    else:
        full_path = Path(file_path)

    if not full_path.exists():
        raise FileNotFoundError(f"Memory file not found: {full_path}")

    import re
    import yaml

    content = full_path.read_text(encoding="utf-8")

    # Extract frontmatter
    frontmatter = {}
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        except Exception:
            pass

        # Remove frontmatter from content
        content = content[match.end():]

    # Calculate relative path as string
    try:
        relative_path = str(full_path.relative_to(memory_dir))
    except ValueError:
        # Not relative to memory_dir
        relative_path = full_path.name

    return {
        "file_path": str(full_path),
        "relative_path": relative_path,
        "content": content.strip(),
        "frontmatter": frontmatter,
    }


def upsert_memory(
    file_path: str,
    scope: str = None,
    memory_type: str = None,
    metadata: dict = None,
    domain_tags: list = None,
    trust_metadata: dict = None,
) -> str:
    """
    Upsert a memory to the vector database.

    Args:
        file_path: Path to memory file
        scope: Memory scope (auto-detected from file if None)
        memory_type: Memory type (auto-detected from file if None)
        metadata: Additional metadata
        domain_tags: Domain/technical tags (e.g., ["RAP", "CDS"])
        trust_metadata: Trust metadata dict (source_type, approval_status, etc.)

    Returns:
        ID of upserted memory.
    """
    config = get_config()

    # Load memory file
    data = load_memory_file(file_path)

    # Get type and scope from frontmatter or params
    frontmatter = data["frontmatter"]
    memory_type = memory_type or frontmatter.get("type", "other")
    scope = scope or frontmatter.get("scope", f"{config['default_scope']}:default")

    # Build base metadata
    memory_metadata = {
        "source": frontmatter.get("source", "file"),
        "author": frontmatter.get("author", ""),
        "created_at": frontmatter.get("created_at", int(time.time())),
        "provenance_weight": frontmatter.get("provenance_weight", 0.5),
        "workspace": frontmatter.get("workspace", ""),
        "pinned": frontmatter.get("pinned", False),
    }
    if metadata:
        memory_metadata.update(metadata)

    # Extract trust metadata from frontmatter or params
    trust_kwargs = {}
    if trust_metadata:
        trust_kwargs.update(trust_metadata)

    # Check frontmatter for trust fields
    for key in ["source_type", "approval_status", "confidence", "last_validated",
                "owner", "supersedes", "superseded_by"]:
        if key in frontmatter:
            trust_kwargs[key] = frontmatter[key]

    # Create trust metadata
    trust = TrustMetadata(**trust_kwargs)

    # Extract domain tags from frontmatter or params
    tags = domain_tags or frontmatter.get("domain_tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    # Create memory object
    memory = Memory(
        file_path=data["relative_path"],
        scope=scope,
        type=memory_type,
        content=data["content"],
        metadata=memory_metadata,
        domain_tags=tags,
        trust=trust,
    )

    # Initialize providers
    embedder = OllamaEmbedder(
        base_url=config["ollama_base_url"],
        model=config["embedding_model"],
    )

    qdrant = QdrantProvider(
        host=config["qdrant_host"],
        port=config["qdrant_port"],
        collection=config["qdrant_collection"],
        embedding_dim=config["embedding_dim"],
        api_key=config["qdrant_api_key"] or None,
    )
    qdrant.initialize()

    # Generate embedding
    # Use content, type, scope, and domain tags for better semantic matching
    tags_str = ", ".join(memory.domain_tags) if memory.domain_tags else ""
    text_to_embed = f"{data['content']}\n\nType: {memory_type}\nScope: {scope}\nTags: {tags_str}"
    memory.embedding = embedder.embed(text_to_embed)

    # Store content and trust/domain metadata in payload for retrieval
    memory.metadata["content"] = data["content"]
    memory.metadata["domain_tags"] = memory.domain_tags
    memory.metadata["source_type"] = memory.trust.source_type
    memory.metadata["approval_status"] = memory.trust.approval_status
    memory.metadata["confidence"] = memory.trust.confidence
    if memory.trust.owner:
        memory.metadata["owner"] = memory.trust.owner
    if memory.trust.last_validated:
        memory.metadata["last_validated"] = memory.trust.last_validated
    if memory.trust.supersedes:
        memory.metadata["supersedes"] = memory.trust.supersedes
    if memory.trust.superseded_by:
        memory.metadata["superseded_by"] = memory.trust.superseded_by

    # Upsert
    memory_id = qdrant.upsert(memory)

    return memory_id


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Upsert memories to AgentBrain")
    parser.add_argument("file", help="Path to memory file")
    parser.add_argument("--scope", help="Memory scope (e.g., user:bob, team:platform)")
    parser.add_argument("--type", choices=["user", "feedback", "project", "reference"],
                        help="Memory type")
    parser.add_argument("--domain-tags", nargs="+",
                        help="Domain tags (e.g., RAP CDS ABAP_Cloud)")
    parser.add_argument("--source-type",
                        choices=["manual", "pr", "adr", "incident", "conversation", "auto_captured"],
                        help="Source type for trust metadata")
    parser.add_argument("--approval-status",
                        choices=["draft", "approved", "archived", "superseded"],
                        default="draft",
                        help="Approval status")
    parser.add_argument("--confidence", type=float, default=0.5,
                        help="Confidence score (0.0 to 1.0)")
    parser.add_argument("--owner", help="Owner of this memory")

    args = parser.parse_args()

    try:
        # Build trust metadata from args
        trust_meta = {}
        if args.source_type:
            trust_meta["source_type"] = args.source_type
        if args.approval_status:
            trust_meta["approval_status"] = args.approval_status
        if args.confidence:
            trust_meta["confidence"] = args.confidence
        if args.owner:
            trust_meta["owner"] = args.owner

        memory_id = upsert_memory(
            file_path=args.file,
            scope=args.scope,
            memory_type=args.type,
            domain_tags=args.domain_tags,
            trust_metadata=trust_meta if trust_meta else None,
        )

        print(f"Upserted memory: {memory_id}")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OllamaEmbedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
