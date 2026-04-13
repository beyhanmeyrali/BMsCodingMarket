---
name: honcho-install
description: Install Ollama and required models for honcho-local plugin
---

# Honcho Local Installation

This command installs Ollama (if needed) and pulls the required models for the honcho-local plugin.

## What gets installed

1. **Ollama** - Local LLM runner (if not already installed)
2. **qwen3.5:9b** - Chat model with thinking support
3. **qwen3-embedding:0.6b** - Embedding model for semantic search
4. **Python dependencies** - ollama, psycopg2-binary

## Usage

Run this command to install everything:
```
/honcho-install
```

## What happens

The setup script will:
1. Check if Ollama is installed and running
2. Download qwen3.5:9b model (~5GB)
3. Download qwen3-embedding:0.6b model (~400MB)
4. Install Python dependencies via pip
5. Verify everything works

## Manual installation

If the automatic setup fails, you can install manually:

```bash
# Install Ollama
# Download from https://ollama.ai or use:
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull models
ollama pull qwen3.5:9b
ollama pull qwen3-embedding:0.6b

# Install Python dependencies
pip install ollama psycopg2-binary
```

## Verification

After installation, run `/honcho-check` to verify everything is working.

## Troubleshooting

**Ollama not found**: Make sure Ollama is installed and in your PATH
**Port already in use**: Ollama uses port 11434. Check if another process is using it
**Download fails**: Check your internet connection and disk space (~6GB needed)
**Python errors**: Make sure you're using Python 3.10+
