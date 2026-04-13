---
name: honcho-install
description: Install official Honcho memory system with Ollama locally. Sets up Postgres database, Honcho server (via Docker), and Ollama for 100% local AI agent memory.
---

# Honcho + Ollama Local Installation

This command installs the official Honcho memory system with Ollama for 100% local AI agent memory.

> **Windows users:** The Honcho server must run via Docker — it uses Linux-only system calls (`fcntl`) and cannot run natively on Windows. The Docker approach works on all platforms.

## What Gets Installed

1. **Ollama** - Local LLM runner (qwen3.5:9b for chat, qwen3-embedding for search)
2. **PostgreSQL + pgvector** - Database for Honcho storage (via Docker)
3. **Honcho server** - Official FastAPI memory service (via Docker)
4. **Honcho SDK** - Python client (`honcho-ai`)

## Quick Install

```bash
# 1. Install Ollama and pull models
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:9b
ollama pull qwen3-embedding:0.6b
ollama serve &

# 2. Install Honcho SDK
pip install honcho-ai pyyaml

# 3. Clone Honcho and start via Docker Compose (works on Windows/Mac/Linux)
git clone https://github.com/plastic-labs/honcho.git
cd honcho
cp .env.template .env
cp docker-compose.yml.example docker-compose.yml
```

Edit `.env` with these minimal settings:
```bash
DB_CONNECTION_URI=postgresql+psycopg://honcho:honcho_password@database:5432/honcho_dev
LLM_OPENAI_COMPATIBLE_BASE_URL=http://host.docker.internal:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=sk-placeholder
EMBED_MESSAGES=false
DERIVER_ENABLED=false
SUMMARY_ENABLED=false
DREAM_ENABLED=false
AUTH_USE_AUTH=false
```

```bash
# 4. Build and start the full stack (Postgres + Redis + Honcho FastAPI server)
# --build is required on first run — there's no pre-built image, it builds from source
docker compose up -d --build

# Server starts at http://localhost:8000
```

## Verify Installation

```bash
curl http://localhost:8000/health
```

```python
from honcho import Honcho

honcho = Honcho(base_url="http://localhost:8000", workspace_id="test")
user = honcho.peer("test-user")
print(f"Created peer: {user.id}")
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Your App   │────▶│   Honcho    │────▶│  Postgres   │
│             │     │  (Docker)   │     │  (Docker)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Ollama    │
                    │ (local)     │
                    └─────────────┘
```

## Next Steps

- Use `/honcho-export` to export memory to wiki format
- Use `/honcho-import` to import wiki knowledge into Honcho
