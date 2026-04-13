---
name: honcho-install
description: Install official Honcho memory system with Ollama locally. Sets up Postgres database, Honcho server, and Ollama for 100% local AI agent memory.
---

# Honcho + Ollama Local Installation

This command installs the official Honcho memory system with Ollama for 100% local AI agent memory.

## What Gets Installed

1. **Ollama** - Local LLM runner (qwen3.5:9b for chat, qwen3-embedding for search)
2. **PostgreSQL + pgvector** - Database for Honcho storage
3. **Honcho** - Official memory library for AI agents
4. **Honcho SDK** - Python client (honcho-ai)

## Quick Install

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull models
ollama pull qwen3.5:9b
ollama pull qwen3-embedding:0.6b

# 3. Start Ollama
ollama serve

# 4. Install Honcho SDK
pip install honcho-ai psycopg2-binary

# 5. Start Postgres with pgvector (Docker)
docker run -d \
  --name honcho-postgres \
  -e POSTGRES_PASSWORD=honcho123 \
  -e POSTGRES_DB=honcho_db \
  -p 5432:5432 \
  -v honcho_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

# 6. Set environment variables
export HONCHO_BASE_URL="http://localhost:8000"
export DB_CONNECTION_URI="postgresql+psycopg://postgres:honcho123@localhost:5432/honcho_db"
export LLM_OPENAI_API_BASE="http://localhost:11434/v1"
export LLM_OPENAI_API_KEY="sk-placeholder"  # Ollama doesn't need real key
export EMBEDDING_MODEL="qwen3-embedding:0.6b"
export EMBEDDING_PROVIDER="openai"

# 7. Clone and run Honcho server
git clone https://github.com/plastic-labs/honcho.git
cd honcho
cp .env.template .env
# Edit .env with your DB_CONNECTION_URI and LLM settings
uv run alembic upgrade head
uv run fastapi dev src/main.py
```

## Verify Installation

```python
from honcho import Honcho

# Test connection
honcho = Honcho(workspace_id="test")

# Create a peer
user = honcho.peer("test-user")
print(f"Created peer: {user.id}")

# Success!
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Your App   │────▶│   Honcho    │────▶│  Postgres   │
│             │     │   (FastAPI) │     │  + pgvector │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Ollama    │
                    │ (qwen3.5)   │
                    └─────────────┘
```

## Next Steps

- Use `/honcho-export` to export memory to wiki format
- Use `/honcho-import` to import wiki knowledge into Honcho
