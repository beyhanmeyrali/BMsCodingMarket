"""
Embedding Generation Script

Generates embeddings for text using Ollama models.
Can embed single text or batch process multiple texts.
"""

import os
import sys
import json
from pathlib import Path

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.ollama import OllamaEmbedder, OllamaEmbedError


def get_config() -> dict:
    """Get configuration from environment variables."""
    return {
        "ollama_base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "embedding_model": os.environ.get("EMBEDDING_MODEL", "qwen3:0.6b"),
    }


def embed_text(text: str) -> list[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Input text

    Returns:
        Embedding vector.
    """
    config = get_config()

    embedder = OllamaEmbedder(
        base_url=config["ollama_base_url"],
        model=config["embedding_model"],
    )

    return embedder.embed(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.

    Args:
        texts: List of input texts

    Returns:
        List of embedding vectors.
    """
    config = get_config()

    embedder = OllamaEmbedder(
        base_url=config["ollama_base_url"],
        model=config["embedding_model"],
    )

    return embedder.embed_batch(texts)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings using Ollama")
    parser.add_argument("text", nargs="?", help="Text to embed")
    parser.add_argument("--file", type=str, help="Read text from file")
    parser.add_argument("--batch", action="store_true", help="Batch mode (read JSON from stdin)")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                        help="Output format")

    args = parser.parse_args()

    # Get text to embed
    if args.batch:
        # Batch mode: read JSON array from stdin
        texts = json.loads(sys.stdin.read())
        if isinstance(texts, str):
            texts = [texts]
        embeddings = embed_batch(texts)

        if args.output == "json":
            output = [{"text": t, "embedding": e} for t, e in zip(texts, embeddings)]
            print(json.dumps(output, indent=2))
        else:
            for e in embeddings:
                print(json.dumps(e))

    elif args.file:
        # Read from file
        text = Path(args.file).read_text(encoding="utf-8")
        embedding = embed_text(text)

        if args.output == "json":
            print(json.dumps({"embedding": embedding}, indent=2))
        else:
            print(json.dumps(embedding))

    elif args.text:
        # Direct text
        embedding = embed_text(args.text)

        if args.output == "json":
            print(json.dumps({"embedding": embedding}, indent=2))
        else:
            print(json.dumps(embedding))

    else:
        # Read from stdin
        text = sys.stdin.read()
        if text:
            embedding = embed_text(text)

            if args.output == "json":
                print(json.dumps({"embedding": embedding}, indent=2))
            else:
                print(json.dumps(embedding))


if __name__ == "__main__":
    try:
        main()
    except OllamaEmbedError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
