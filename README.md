# Honcho Bridge for Claude Code

> **Claude Code plugin for using official Honcho memory system locally with Ollama - no API keys, fully offline.**

## What is Honcho Bridge?

**Honcho Bridge** helps Claude Code use the official [Honcho](https://github.com/plastic-labs/honcho) memory system with local Ollama models.

**The Problem:** Official Honcho plugin exists but doesn't guide Claude Code on local setup with Ollama + Docker Postgres.

**The Solution:** This plugin provides:
1. **Clear guidance** for Claude Code on using Honcho locally
2. **Wiki bridge skills** - Export/import memory to markdown (Karpathy LLM Wiki pattern)
3. **100% local** - No API keys, works offline

## Quick Overview

```mermaid
flowchart LR
    subgraph Claude_Code
        Agent[AI Agent]
    end

    subgraph Honcho_Bridge
        Guide[Skills: How to use Honcho locally]
        Export[/honcho-export]
        Import[/honcho-import]
    end

    subgraph Local_Stack
        Honcho[Honcho Server]
        Postgres[Postgres + pgvector]
        Ollama[Ollama - qwen3.5:9b]
    end

    Agent -->|Reads skills| Guide
    Agent -->|Exports memory| Export
    Agent -->|Imports knowledge| Import
    Guide -->|Configures| Honcho
    Honcho -->|Stores in| Postgres
    Honcho -->|Queries| Ollama

    style Guide fill:#e1f5fe
    style Export fill:#f3e5f5
    style Import fill:#f3e5f5
```

## Features

| Feature | Description |
|---------|-------------|
| **Local Honcho Guide** | Skills that teach Claude Code how to use Honcho with Ollama |
| **Wiki Export** | Export agent memory to Obsidian-compatible markdown |
| **Wiki Import** | Import documentation into agent memory |
| **100% Local** | No API keys, works offline |
| **Postgres + pgvector** | Vector search for semantic memory retrieval |

## Installation

### One-Time Setup (Run in Claude Code)

#### 1. Add the Marketplace

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
```

#### 2. Install the Plugin

```
/plugin install honcho-bridge@bms-marketplace
```

#### 3. Install Dependencies

```
/honcho-install
```

This installs:
- **Ollama** (qwen3.5:9b model)
- **Honcho full stack via Docker Compose** (FastAPI server + Postgres + Redis)
- **Python dependencies** (`honcho-ai`, `pyyaml`)

## How It Works

### 1. Agent Uses Honcho Memory

When your agent needs memory, Claude Code reads the `use-honcho-locally` skill which provides:

```python
from honcho import Honcho

# Initialize with local server
honcho = Honcho(
    workspace_id="my-agent",
    base_url="http://localhost:8000"
)

# Create peers (users and agents are both "peers")
user = honcho.peer("user-123")
agent = honcho.peer("assistant")

# Add conversation
session = honcho.session("conv-1")
session.add_messages([
    user.message("I need help with Python"),
    agent.message("I can help with that"),
])

# Query user behavior
response = user.chat("What does this user need?")
# Returns: "The user is learning Python programming"
```

### 2. Export Memory to Wiki

```
/honcho-export
```

Runs `to_wiki.py --base-url http://localhost:8000 --workspace <id>`.

Creates `wiki/` folder with:
- `peers/*.md` - User profiles
- `sessions/*.md` - Conversation transcripts
- `index.md` - Catalog

View in **Obsidian** to see graph view and connections!

### 3. Import Wiki to Memory

```
/honcho-import
```

Runs `wiki_to_honcho.py --base-url http://localhost:8000 --workspace <id> --wiki wiki/`.

Imports existing documentation into Honcho for agent knowledge.

## Why Wiki Bridge?

**Problem:** Agent memory is locked in databases - humans can't read or edit it.

**Solution:** Export to markdown so you can:
- **Verify** what your agent "knows"
- **Edit** incorrect memories
- **Build** knowledge bases from conversations
- **Bootstrap** agents from existing docs

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Claude Code │────▶│   Honcho    │────▶│  Postgres   │
│   Agent     │     │   (FastAPI) │     │  + pgvector │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │
       │                    ▼
       │             ┌─────────────┐
       │             │   Ollama    │
       └────────────▶│  (qwen3.5)  │
         Wiki sync   └─────────────┘
```

## Skills

| Skill | Purpose |
|-------|---------|
| `use-honcho-locally` | Guides Claude Code on using Honcho with Ollama |
| `honcho-wiki` | Wiki export/import (Karpathy LLM Wiki pattern) |

## Commands

| Command | Purpose |
|---------|---------|
| `/honcho-install` | Install Honcho + Ollama + Postgres |
| `/honcho-export` | Export memory to wiki markdown |
| `/honcho-import` | Import wiki to Honcho memory |

## Comparison

| Aspect | Official Honcho | This Plugin |
|--------|----------------|-------------|
| **Core library** | ✅ Official Honcho | ✅ Uses official Honcho |
| **LLM** | OpenAI/Anthropic (API keys) | **Ollama (local)** |
| **Setup guidance** | ❌ Assumes cloud | ✅ **Local setup instructions** |
| **Wiki export** | ❌ Not included | ✅ **Karpathy wiki pattern** |
| **License** | AGPL-3.0 | MIT (bridge code) |

## Local Setup Details

### Prerequisites

```bash
# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:9b
ollama serve
```

> Postgres is managed by Honcho's Docker Compose — no separate container needed.

### Honcho Server (Docker — required on Windows)

> **Windows:** The Honcho server uses Linux-only system calls and **cannot run natively on Windows**. Use Docker on all platforms.

```bash
git clone https://github.com/plastic-labs/honcho.git
cd honcho
cp .env.template .env
cp docker-compose.yml.example docker-compose.yml
```

**Edit `.env` with these minimal settings:**
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

**Start the stack (builds FastAPI server from source on first run):**
```bash
docker compose up -d --build
```

The server will start at `http://localhost:8000`.

### Verify Setup

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check all Honcho containers
docker compose ps

# Check Honcho server
curl http://localhost:8000/health
```

## Wiki Format

```
wiki/
├── index.md              # Catalog
├── peers/
│   └── user_123.md       # User profile
└── sessions/
    └── session-1.md      # Conversation
```

### Peer Page

```markdown
---
peer_id: user_123
name: Beyhan MEYRALI
---

# Beyhan MEYRALI

## Interests
- Ollama, Python, AI agents

## Communication Style
Direct, technical, prefers concise answers
```

## Troubleshooting

### "Ollama connection failed"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### "Postgres connection failed"
```bash
# Check Docker containers
docker compose ps

# Check logs
docker compose logs database

# Restart if needed
docker compose restart database
```

### "Module 'honcho' not found"
```bash
pip install honcho-ai
```

### Port 8000 already in use
```bash
# Edit docker-compose.yml and change the api port mapping
# ports: - "127.0.0.1:8001:8000"
# Then update base_url to http://localhost:8001
```

## Inspiration

- **[Honcho by Plastic Labs](https://github.com/plastic-labs/honcho)** - Official memory library
- **[LLM Wiki pattern by Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** - Knowledge that compounds
- **[Ollama](https://ollama.com)** - Local LLM inference

## License

MIT License

## Author

Beyhan MEYRALI - [beyhanmeyrali@gmail.com](mailto:beyhanmeyrali@gmail.com)
