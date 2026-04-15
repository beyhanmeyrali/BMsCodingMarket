# BMsCodingMarket

> **Claude Code plugins for local AI development** — Fully offline memory, wiki bridge, workflow automation, and team collaboration.

## Plugins

### Featured: honcho-bridge

**`honcho-bridge`** is a comprehensive Python-based Claude Code plugin for working with a **local Honcho memory system**. It enables persistent AI memory that runs entirely on your machine — no API keys, no cloud, no monthly fees.

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
| **Privacy** | Cloud storage | Local only |
| **Features** | Basic memory | Memory hierarchy, search, team sync |

## Quick Start

### 1. Install Dependencies

```bash
pip install honcho-ai pyyaml python-dotenv
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

**Important:** If you have the official `plastic-labs/claude-honcho` plugin installed, uninstall it first:

```
/plugin marketplace remove plastic-labs/claude-honcho
```

Then install this plugin:

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install honcho-bridge@bms-marketplace
```

## Quick Start: Using the Plugin

### Store Information to Memory

```
/honcho-store "I prefer TypeScript for frontend projects"
```

### Query Your Memory

```
/honcho-query "What are my coding preferences?"
```

### Advanced Search

```
/honcho-search "authentication decisions" --file-pattern "src/auth/*" --after 7d
```

### Get Suggestions

```
/honcho-suggest "I'm implementing user authentication"
```

---

## Commands Reference

| Command | Purpose |
|---------|---------|
| `/honcho-store` | Store facts/preferences to memory |
| `/honcho-query` | Ask what Honcho knows about you |
| `/honcho-status` | Check system health and stats |
| `/honcho-export` | Export workspace to markdown wiki |
| `/honcho-import` | Import markdown wiki back to Honcho |
| `/honcho-install` | Show setup instructions |
| `/honcho-search` | Advanced semantic search with filters |
| `/honcho-suggest` | Get proactive memory suggestions |
| `/honcho-sync` | Sync with Claude native memory |
| `/honcho-health` | Memory health dashboard |
| `/honcho-hierarchy` | Manage memory levels |
| `/honcho-migrate` | Copy/move data between workspaces |
| `/honcho-wipe` | Clear workspace data |

---

## Features Overview

### 🔒 Privacy Controls

- **Automatic redaction** of sensitive information (emails, API keys, passwords, IPs)
- **`.honchoignore`** file for excluding sensitive files from memory
- **Per-session opt-out** capability

```bash
# Enable privacy features
HONCHO_PRIVACY_ENABLED=true
HONCHO_REDACT_PATTERNS=email,api_key,password,ip
```

### 🪝 Enhanced Hooks

The plugin includes 6 automatic hooks that capture context throughout your session:

| Hook | When It Runs | What It Does |
|------|--------------|--------------|
| **SessionStart** | When you start a new Claude session | Loads your context from Honcho + Claude native memory |
| **UserPromptSubmit** | Before sending your prompt to Claude | Detects critical facts (REMEMBER:, never forget) and stores immediately |
| **PostToolUse** | After any tool execution | Tracks tool usage patterns and detects tech stack |
| **PreCompact** | Before context compaction | Summarizes important points to preserve them |
| **SessionEnd** | When session ends | Saves conversation for observation extraction |
| **SubagentStop** | When subagent completes | Captures learnings from delegated work |

### 📊 Memory Hierarchy

Organize memories at different levels for better context:

- **Global**: User preferences across all projects
- **Project**: Project-specific decisions and context
- **File**: Specific file-related knowledge
- **Context**: Session-specific information

```
/honcho-hierarchy store global "I always use TypeScript for new projects"
/honcho-hierarchy query project --scope my-project
```

### 🔄 Claude Native Memory Sync

Bidirectional sync with Claude Code's built-in memory system:

```bash
# Sync both directions
/honcho-sync --mode bidirectional

# Export Honcho to Claude memory
/honcho-sync --mode honcho-to-claude

# Import Claude memory to Honcho
/honcho-sync --mode claude-to-honcho
```

### 🔍 Advanced Search

Semantic search with powerful filters:

```bash
# Search by file pattern
/honcho-search "error handling" --file-pattern "src/**/*.py"

# Search recent memories
/honcho-search "decisions" --after 30d

# Search by memory level
/honcho-search "preferences" --memory-type global
```

### 💊 Memory Health Dashboard

Monitor your memory system health:

```bash
/honcho-health
```

Shows:
- Stale observations (older than 30 days)
- Deriver lag (unprocessed messages)
- Storage trends (growing/stable/shrinking)
- Potential duplicates

### 🏷️ Context-Aware Auto-Tagging

Every memory is automatically tagged with:

- **Git context**: branch, commits, modified files
- **Tech stack**: detected from package.json, requirements.txt, etc.
- **Project type**: nextjs, django, rust-cli, etc.
- **Folder and workspace**: for organization

### 👥 Team Collaboration

Share and merge memories with your team:

```bash
# Export for team review
python scripts/honcho_export_team.py --output team-memory/

# After review and edits, import with conflict resolution
python scripts/honcho_merge_team.py --import-dir team-memory/
```

---

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Core Configuration
HONCHO_WORKSPACE=my-project
HONCHO_PEER_ID=user
HONCHO_BASE_URL=http://localhost:8000

# Privacy
HONCHO_PRIVACY_ENABLED=true
HONCHO_REDACT_PATTERNS=email,api_key,password,ip
HONCHO_SESSION_OPT_OUT=false

# Critical Facts (immediate storage)
HONCHO_IMMEDIATE_STORE=true
HONCHO_CRITICAL_PATTERNS=remember:|never forget|important:

# Claude Sync
HONCHO_CLAUDE_SYNC_MODE=bidirectional

# Memory Hierarchy
HONCHO_MEMORY_LEVEL=project

# Search
HONCHO_SEARCH_THRESHOLD=0.7
HONCHO_SEARCH_DEFAULT_AFTER=30d

# Health Dashboard
HONCHO_STALE_THRESHOLD_DAYS=30
HONCHO_DERIVER_LAG_WARNING_MINUTES=5
```

---

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

---

## Project Structure

```
BMsCodingMarket/
├── plugins/
│   └── honcho-bridge/              # Main plugin
│       ├── commands/               # Slash commands (10+)
│       ├── skills/                 # Reusable skills (6)
│       ├── scripts/                # Python utilities (14)
│       │   ├── honcho_query.py
│       │   ├── honcho_store.py
│       │   ├── honcho_status.py
│       │   ├── honcho_search.py    # Advanced search
│       │   ├── honcho_suggest.py   # Proactive suggestions
│       │   ├── honcho_sync.py      # Claude memory sync
│       │   ├── honcho_hierarchy.py # Memory levels
│       │   ├── honcho_health.py    # Health dashboard
│       │   ├── honcho_export_team.py
│       │   ├── honcho_merge_team.py
│       │   ├── honcho_migrate.py
│       │   ├── honcho_wipe.py
│       │   ├── to_wiki.py
│       │   └── wiki_to_honcho.py
│       ├── hooks/                  # Event automation (6)
│       │   ├── load_memory.py      # SessionStart
│       │   ├── save_messages.py    # SessionEnd
│       │   ├── user_prompt_submit.py
│       │   ├── post_tool_use.py
│       │   ├── pre_compact.py
│       │   ├── subagent_stop.py
│       │   ├── auto_tagger.py      # Context tagging
│       │   └── hooks.json
│       └── privacy/                # Privacy module
│           └── redact.py
├── docs/
│   ├── HONCHO_SETUP_GUIDE.md       # Full local setup guide
│   └── LESSONS_LEARNED.md          # Development lessons
├── .env.example                    # Configuration template
├── .honchoignore.example           # Privacy ignore patterns
└── README.md
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Honcho Setup Guide](docs/HONCHO_SETUP_GUIDE.md) | Complete guide for running Honcho locally with Docker + Ollama on Windows |
| [Lessons Learned](docs/LESSONS_LEARNED.md) | Development insights and troubleshooting |

---

## Why Local Honcho?

- **Privacy** — All conversations and observations stay on your machine
- **No API costs** — Use your own Ollama models (qwen3, llama3, mistral, etc.)
- **Offline** — Works without internet after initial model download
- **Control** — Modify source, customize models, inspect everything
- **Speed** — Local inference can be faster than cloud API calls
- **Compliance** — Keep sensitive code and discussions in-house
- **Team Ready** — Export/import workflows for team knowledge sharing

---

## Requirements

- **Docker Desktop** (Linux containers mode)
- **Ollama** — Local inference server
- **Python 3.10+** with `pip`
- **Claude Code** — CLI or desktop app

---

## Links

- [Honcho](https://github.com/plastic-labs/honcho) — The memory platform
- [claude-honcho](https://github.com/plastic-labs/claude-honcho) — Official cloud plugin
- [Ollama](https://ollama.com) — Local LLM runner

---

## License

MIT

---

## Coming Soon: AgentBrain

**`agentbrain`** is an enterprise-grade persistent memory system for Claude Code. It enables teams to share knowledge, conventions, and context across sessions and projects.

### Features

- **Persistent memory** — Sessions end, learnings remain
- **Shared knowledge** — Team and project-level memory layers
- **Semantic retrieval** — Vector DB finds relevant memories automatically
- **Auto-curation** — Subagents summarize, categorize, and dedup
- **100% self-hosted** — Your data, your infra, free/OSS tools only

### Status

🚧 **In Development** — See [`docs/AgentBrain/`](docs/AgentBrain/) for design and implementation plan.

**Author:** [Beyhan Meyrali](https://github.com/beyhanmeyrali)
