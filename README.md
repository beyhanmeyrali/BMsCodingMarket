# BMsCodingMarket

> **Claude Code plugins for local AI development** — Fully offline memory, wiki bridge, and workflow automation.

## Featured Plugin: honcho-bridge

**`honcho-bridge`** is a Python-based Claude Code plugin for working with a **local Honcho memory system**. It enables persistent AI memory that runs entirely on your machine — no API keys, no cloud, no monthly fees.

### Why honcho-bridge?

The official [plastic-labs/claude-honcho](https://github.com/plastic-labs/claude-honcho) plugin is great for cloud usage, but it requires `bun` (JavaScript runtime) and connects to a paid cloud service. `honcho-bridge` is built for developers who want:

- **100% offline** operation — your data never leaves your machine
- **No API costs** — use your own Ollama models
- **Python native** — no bun, node, or JavaScript runtimes needed
- **Full control** — modify, extend, and inspect everything

| | Official Plugin | honcho-bridge |
|---|---|---|
| **Runtime** | bun (JavaScript) | Python |
| **Backend** | app.honcho.dev (cloud) | localhost:8000 (Docker) |
| **API Key** | Required | Not needed |
| **Internet** | Required | Fully offline |
| **LLM** | Cloud (paid per token) | Ollama (local, free) |
| **Best for** | Quick cloud setup | Privacy, offline, local LLMs |

## Quick Start

### 1. Install Dependencies

```bash
pip install honcho-ai pyyaml
```

### 2. Start Local Honcho (Docker + Ollama)

Follow the full setup guide: **[`docs/HONCHO_SETUP_GUIDE.md`](docs/HONCHO_SETUP_GUIDE.md)**

```powershell
git clone https://github.com/plastic-labs/honcho.git E:\workspace\honcho
cd E:\workspace\honcho
# Apply patches, configure .env, then:
docker compose up -d --build
```

### 3. Install the Plugin

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install honcho-bridge@bms-marketplace
```

## Skills & Commands

### Skills

| Skill | Purpose |
|-------|---------|
| `honcho-query` | Query what Honcho learned about a user via `peer.chat()` |
| `honcho-store` | Store messages for memory extraction and observation |
| `honcho-status` | Check system health, statistics, and deriver status |
| `honcho-wipe` | Clear workspace data (destructive, requires confirmation) |
| `honcho-migrate` | Copy/move data between workspaces |
| `honcho-wiki` | Export/import memory to Obsidian-compatible markdown |

### Commands

| Command | Description |
|---------|-------------|
| `/honcho-export` | Export Honcho workspace to markdown wiki |
| `/honcho-import` | Import markdown wiki back into Honcho |
| `/honcho-install` | Show local setup instructions |

### Automatic Hooks

The plugin includes automatic memory hooks — no manual commands needed:

| Hook | When It Runs | What It Does |
|------|--------------|--------------|
| **SessionStart** | When you start a new Claude session | Loads your context from Honcho memory |
| **SessionEnd** | When session ends | Saves conversation for observation extraction |

**Configure hooks** by setting environment variables:

```bash
# In your system environment or .env file
HONCHO_WORKSPACE=my-project       # Your workspace ID
HONCHO_PEER_ID=user               # Your peer identifier
HONCHO_BASE_URL=http://localhost:8000  # Local Honcho API
```

**Note:** If using honcho-bridge, uninstall the official `plastic-labs/claude-honcho` plugin to avoid hook conflicts.

## Usage Examples

```bash
# Check system health
python plugins/honcho-bridge/scripts/honcho_status.py \
  --workspace my-project

# Store a message for memory extraction
python plugins/honcho-bridge/scripts/honcho_store.py \
  --workspace my-project --peer alice --session test \
  --message "I prefer Neovim for TypeScript development"

# Query what Honcho learned (wait ~1 min after storing)
python plugins/honcho-bridge/scripts/honcho_query.py \
  --workspace my-project --peer alice \
  --query "What editor does this user prefer?"

# Export to wiki for inspection
python plugins/honcho-bridge/scripts/to_wiki.py \
  --workspace my-project --output wiki/

# Import edited wiki back to Honcho
python plugins/honcho-bridge/scripts/wiki_to_honcho.py \
  --workspace my-project --wiki wiki/
```

## How Honcho Memory Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Session 1                                    │
│  "I use TypeScript, prefer Neovim, work in fintech"            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Honcho Deriver                                │
│  (background worker, runs every ~1 minute)                      │
│                                                                 │
│  • Reads messages                                               │
│  • Calls local LLM (Ollama)                                     │
│  • Extracts structured observations                             │
│  • Stores with vector embeddings                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Observations                                 │
│  • User prefers TypeScript                                      │
│  • User uses Neovim as editor                                   │
│  • User works in fintech industry                               │
│  • User prefers concise answers                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Session 2 (later)                            │
│  "Help me add auth"                                             │
│                                                                 │
│  Agent already knows: TypeScript stack, Neovim, fintech        │
│  No need to repeat context!                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
BMsCodingMarket/
├── plugins/
│   └── honcho-bridge/          # Main plugin
│       ├── commands/            # Slash commands
│       ├── skills/              # Reusable skills
│       ├── scripts/             # Python utilities
│       │   ├── honcho_query.py
│       │   ├── honcho_store.py
│       │   ├── honcho_status.py
│       │   ├── honcho_wipe.py
│       │   ├── honcho_migrate.py
│       │   ├── to_wiki.py
│       │   └── wiki_to_honcho.py
│       └── hooks/               # Event automation
├── docs/
│   └── HONCHO_SETUP_GUIDE.md    # Full local setup guide
└── README.md
```

## Documentation

| Document | Description |
|----------|-------------|
| [Honcho Setup Guide](docs/HONCHO_SETUP_GUIDE.md) | Complete guide for running Honcho locally with Docker + Ollama on Windows |

## Why Local Honcho?

- **Privacy** — All conversations and observations stay on your machine
- **No API costs** — Use your own Ollama models (qwen3, llama3, mistral, etc.)
- **Offline** — Works without internet after initial model download
- **Control** — Modify source, customize models, inspect everything
- **Speed** — Local inference can be faster than cloud API calls
- **Compliance** — Keep sensitive code and discussions in-house

## Requirements

- **Docker Desktop** (Linux containers mode)
- **Ollama** — Local inference server
- **Python 3.10+** with `pip`
- **Claude Code** — CLI or desktop app

## Links

- [Honcho](https://github.com/plastic-labs/honcho) — The memory platform
- [claude-honcho](https://github.com/plastic-labs/claude-honcho) — Official cloud plugin
- [Ollama](https://ollama.com) — Local LLM runner

## License

MIT

---

**Author:** [Beyhan Meyrali](https://github.com/beyhanmeyrali)
