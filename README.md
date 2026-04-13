# honcho-bridge

> **Fully local Honcho memory integration for Claude Code** — no API key, no cloud, just your own Docker + Ollama stack.

**Why this exists:** The official [plastic-labs/claude-honcho](https://github.com/plastic-labs/claude-honcho) plugin is excellent for cloud usage, but it requires `bun` (a JavaScript runtime) and connects to the paid Honcho cloud service. For developers who want **100% local, offline memory** with their own Ollama models, the official plugin doesn't fit.

`honcho-bridge` provides a Python-based alternative with skills and scripts that work directly with your local Honcho API at `localhost:8000`.

## What this is

A Claude Code plugin for working with a **local Honcho memory system** running via Docker + Ollama. It provides:

- **Skills** for querying, storing, and managing memory
- **Wiki export/import** to readable Obsidian-compatible markdown
- **Full offline operation** — no API keys, no internet required

## Cloud vs Local

| | Official Plugin | honcho-bridge |
|---|---|---|
| **Runtime** | bun (JavaScript) | Python |
| **Backend** | app.honcho.dev (cloud) | localhost:8000 (Docker) |
| **API Key** | Required | Not needed |
| **Internet** | Required | Fully offline |
| **LLM** | Cloud (paid) | Ollama (local) |
| **Best for** | Quick setup, cloud users | Privacy, offline, local LLMs |

## Setup

### 1. Run local Honcho (Docker + Ollama)

Follow the full setup guide in **[`docs/HONCHO_SETUP_GUIDE.md`](docs/HONCHO_SETUP_GUIDE.md)**:

```powershell
# Clone Honcho server
git clone https://github.com/plastic-labs/honcho.git E:\workspace\honcho

# Apply source patches for local Ollama
# Configure .env for localhost:8000
# Run with Docker
docker compose up -d --build
```

### 2. Install this plugin

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install honcho-bridge@bms-marketplace
```

### 3. Install Python dependencies

```bash
pip install honcho-ai pyyaml
```

## Skills

| Skill | Purpose |
|-------|---------|
| `honcho-query` | Query what Honcho learned about a user |
| `honcho-store` | Store messages for memory extraction |
| `honcho-status` | Check system health and statistics |
| `honcho-wipe` | Clear workspace data (destructive) |
| `honcho-migrate` | Copy/move data between workspaces |
| `honcho-wiki` | Export/import to Obsidian markdown |

## Commands

| Command | Description |
|---------|-------------|
| `/honcho-export` | Export Honcho workspace to markdown wiki |
| `/honcho-import` | Import markdown wiki back into Honcho |
| `/honcho-install` | Show local setup instructions |

## Quick Start

```bash
# Check system health
python plugins/honcho-bridge/scripts/honcho_status.py --workspace my-project

# Store a message
python plugins/honcho-bridge/scripts/honcho_store.py \
  --workspace my-project --peer alice --session test \
  --message "I prefer Neovim for TypeScript development"

# Wait ~1 minute for deriver, then query
python plugins/honcho-bridge/scripts/honcho_query.py \
  --workspace my-project --peer alice \
  --query "What editor does this user prefer?"

# Export to wiki for inspection
python plugins/honcho-bridge/scripts/to_wiki.py \
  --workspace my-project --output wiki/
```

## Why Local Honcho?

Running Honcho locally gives you:

- **Privacy** — All data stays on your machine
- **No API costs** — Use your own Ollama models
- **Offline** — Works without internet
- **Control** — Modify source, customize models
- **Speed** — Local inference can be faster than cloud

## Links

- [Honcho](https://github.com/plastic-labs/honcho) — the memory platform
- [Setup Guide](docs/HONCHO_SETUP_GUIDE.md) — full local Docker + Ollama instructions
- [claude-honcho](https://github.com/plastic-labs/claude-honcho) — official cloud plugin
