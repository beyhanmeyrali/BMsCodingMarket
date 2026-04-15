"""
Memory Query Script

Performs semantic search on memories with scope-based filtering.
Returns relevant memories based on query meaning, not just keywords.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.ollama import OllamaEmbedder, OllamaEmbedError
from providers.qdrant import QdrantProvider
from providers.base import SearchResult


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
        "embedding_model": os.environ.get("EMBEDDING_MODEL", "qwen3:0.6b"),
        "embedding_dim": int(os.environ.get("EMBEDDING_DIMENSION", "768")),
        # Query config
        "top_k": int(os.environ.get("RETRIEVAL_TOP_K", "8")),
        "min_score": float(os.environ.get("RETRIEVAL_MIN_SCORE", "0.6")),
    }


def get_allowed_scopes() -> List[str]:
    """
    Compute allowed scopes based on environment and git context.

    Returns:
        List of scope filters (e.g., ["user:bob", "team:platform"]).
    """
    scopes = []

    # Always include user scope
    user_id = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    scopes.append(f"user:{user_id}")

    # Add team scope if configured
    if team_id := os.environ.get("AGENTBRAIN_TEAM_ID"):
        scopes.append(f"team:{team_id}")

    # Add org scope if configured
    if org_id := os.environ.get("AGENTBRAIN_ORG_ID"):
        scopes.append(f"org:{org_id}")

    # Add project scope if in a git repo
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            repo_path = Path(result.stdout.strip())
            project_name = repo_path.name
            scopes.append(f"project:{project_name}")
    except Exception:
        pass

    return scopes


def load_memory_content(file_path: str) -> str:
    """
    Load memory content from file.

    Args:
        file_path: Path to memory file

    Returns:
        File content or empty string if not found.
    """
    memory_dir = Path(os.environ.get("MEMORY_DIR", "~/.claude/memory")).expanduser()
    full_path = memory_dir / file_path

    if full_path.exists():
        try:
            return full_path.read_text(encoding="utf-8")
        except Exception:
            pass

    return ""


def query_memories(
    query: str,
    scopes: Optional[List[str]] = None,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
) -> List[SearchResult]:
    """
    Query memories with semantic search.

    Args:
        query: Search query text
        scopes: Allowed scopes (auto-detected if None)
        top_k: Maximum results (from config if None)
        min_score: Minimum similarity score (from config if None)

    Returns:
        List of search results sorted by relevance.
    """
    config = get_config()

    if scopes is None:
        scopes = get_allowed_scopes()
    if top_k is None:
        top_k = config["top_k"]
    if min_score is None:
        min_score = config["min_score"]

    # Initialize providers
    try:
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

    except OllamaEmbedError as e:
        print(f"Warning: Ollama not available: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Failed to initialize providers: {e}", file=sys.stderr)
        return []

    # Generate query embedding
    try:
        query_embedding = embedder.embed(query)
    except OllamaEmbedError as e:
        print(f"Warning: Failed to embed query: {e}", file=sys.stderr)
        return []

    # Search in Qdrant
    try:
        results = qdrant.query(
            embedding=query_embedding,
            scopes=scopes,
            top_k=top_k,
            min_score=min_score,
        )

        # Load full content for each result
        for result in results:
            if result.memory.content:
                # Content already in payload
                continue
            # Load from file
            content = load_memory_content(result.memory.file_path)
            result.memory.content = content

        return results

    except Exception as e:
        print(f"Warning: Query failed: {e}", file=sys.stderr)
        return []


def format_results(results: List[SearchResult]) -> str:
    """
    Format search results as markdown.

    Args:
        results: Search results

    Returns:
        Formatted markdown string.
    """
    if not results:
        return "# No relevant memories found.\n"

    lines = [
        f"# Relevant Memories ({len(results)} found)",
        "",
        "> Retrieved from AgentBrain based on semantic similarity.",
        "",
    ]

    for i, result in enumerate(results, 1):
        memory = result.memory

        # Header with file and score
        score_pct = int(result.score * 100)
        lines.append(f"## {i}. {memory.file_path} (relevance: {score_pct}%)")

        # Metadata
        meta_lines = []
        if memory.scope:
            meta_lines.append(f"**Scope:** {memory.scope}")
        if memory.type:
            meta_lines.append(f"**Type:** {memory.type}")

        if meta_lines:
            lines.append(" | ".join(meta_lines))

        lines.append("")

        # Content (truncated if long)
        content = memory.content or ""
        if len(content) > 2000:
            content = content[:2000] + "\n\n... (truncated)"

        lines.append(content)
        lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Query AgentBrain memories")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--scopes", nargs="+", help="Allowed scopes")
    parser.add_argument("--top-k", type=int, help="Maximum results")
    parser.add_argument("--min-score", type=float, help="Minimum similarity score")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format")

    args = parser.parse_args()

    # Query
    results = query_memories(
        query=args.query,
        scopes=args.scopes,
        top_k=args.top_k,
        min_score=args.min_score,
    )

    # Output
    if args.format == "json":
        import json
        output = [{
            "score": r.score,
            "file": r.memory.file_path,
            "scope": r.memory.scope,
            "type": r.memory.type,
            "content": r.memory.content[:500],  # Truncate for JSON
        } for r in results]
        print(json.dumps(output, indent=2))
    else:
        print(format_results(results))

    return len(results)


if __name__ == "__main__":
    sys.exit(main() if len(sys.argv) > 1 else 0)
