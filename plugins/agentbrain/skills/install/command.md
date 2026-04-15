# AgentBrain Installation Command

```bash
#!/usr/bin/env python3
"""
AgentBrain Installation Script

Automatically installs and configures AgentBrain memory system.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))


def check_docker() -> bool:
    """Check if Docker is available."""
    try:
        subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def start_qdrant() -> bool:
    """Start Qdrant using Docker."""
    docker_dir = plugin_root / "docker"
    compose_file = docker_dir / "qdrant-compose.yml"

    if not compose_file.exists():
        return False

    try:
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d"],
            check=True,
            timeout=30,
        )
        return True
    except Exception:
        return False


def pull_embedding_model() -> bool:
    """Pull the required Ollama embedding model."""
    try:
        subprocess.run(
            ["ollama", "pull", "qwen3-embedding:0.6b"],
            check=True,
            timeout=120,
        )
        return True
    except Exception:
        return False


def test_qdrant() -> bool:
    """Test Qdrant connection."""
    try:
        from providers.qdrant import QdrantProvider

        qdrant = QdrantProvider(
            host="localhost",
            port=6333,
            collection="agentbrain_memories",
            embedding_dim=1024,
        )
        return qdrant.health_check()
    except Exception:
        return False


def test_ollama() -> bool:
    """Test Ollama embedding."""
    try:
        from providers.ollama import OllamaEmbedder

        embedder = OllamaEmbedder(model="qwen3-embedding:0.6b")
        embedding = embedder.embed("test")
        return len(embedding) == 1024
    except Exception:
        return False


def enable_session_start_hook() -> bool:
    """Enable SessionStart hook for automatic memory injection."""
    try:
        hooks_file = plugin_root / "hooks" / "hooks.json"

        if not hooks_file.exists():
            return False

        with open(hooks_file) as f:
            hooks = json.load(f)

        # SessionStart should already be enabled
        return "session-start" in hooks.get("enabled", [])
    except Exception:
        return False


def main():
    """Run installation."""
    print("# AgentBrain Installation\n")
    print("Checking prerequisites...\n")

    # Check Docker
    if not check_docker():
        print("❌ Docker not found. Please install Docker first.")
        print("   Download from: https://www.docker.com/products/docker-desktop/")
        return 1

    print("✅ Docker found")

    # Check Ollama
    if not check_ollama():
        print("\n⚠️  Ollama not running. Starting Ollama...")
        print("   Please start Ollama and run this command again.")
        print("   Download from: https://ollama.ai/")
        return 1

    print("✅ Ollama running")

    # Start Qdrant
    print("\nStarting Qdrant vector database...")
    if not start_qdrant():
        print("❌ Failed to start Qdrant")
        return 1

    print("✅ Qdrant starting (wait a few seconds for it to be ready)")

    # Wait for Qdrant to be ready
    time.sleep(5)

    # Pull embedding model
    print("\nPulling embedding model (this may take a minute)...")
    if not pull_embedding_model():
        print("⚠️  Failed to pull embedding model. You may need to run:")
        print("   ollama pull qwen3-embedding:0.6b")

    # Test connections
    print("\nTesting connections...")

    qdrant_ok = test_qdrant()
    ollama_ok = test_ollama()

    if qdrant_ok:
        print("✅ Qdrant connection successful")
    else:
        print("❌ Qdrant connection failed")

    if ollama_ok:
        print("✅ Ollama embedding working")
    else:
        print("❌ Ollama embedding failed")

    # Check hook
    if enable_session_start_hook():
        print("✅ SessionStart hook enabled")
    else:
        print("⚠️  SessionStart hook may need manual configuration")

    # Summary
    print("\n" + "=" * 50)
    if qdrant_ok and ollama_ok:
        print("✅ AgentBrain installed successfully!")
        print("\nYou can now use:")
        print("  /remember <info>  - Store information")
        print("  /recall <query>   - Retrieve memories")
        print("  /forget <topic>   - Delete a memory")
        print("  /promote <mem> --to <scope>  - Share with team")
        return 0
    else:
        print("⚠️  Installation incomplete. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```
