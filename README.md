# BMsCodingMarket

> **Claude Code plugins for local AI development** — Fully offline memory, wiki bridge, workflow automation, and team collaboration.

## Plugins

### Featured: AgentBrain (NEW!)

**`AgentBrain`** is an enterprise-grade persistent memory system with **semantic retrieval, multi-tenant scoping, and automatic knowledge accumulation**.

Knowledge accumulates automatically — no silos, no manual /remember needed.

```bash
/plugin install agentbrain@bms-marketplace
```

#### Key Features

| Feature | What It Does |
|---------|--------------|
| **Semantic Memory** | Finds relevant context automatically using vector search |
| **Multi-Tenant** | User, team, project, org scopes with proper isolation |
| **Auto-Capture** | Extracts insights from conversations automatically |
| **Auto-Promote** | Frequently accessed memories become team knowledge |
| **100% Offline** | Qdrant + Ollama, zero API costs |
| **Context Rot Prevention** | Decay sweep removes stale memories |
| **Extractors** | Import from PRs, ADRs, incidents |

#### How It Works (Invisible)

```
User: "How do I deploy to production?"

[PreResponse hook runs → Queries Qdrant → Injects memories]

Claude: "Based on our team conventions, we use GitHub Actions..."
```

Knowledge accumulates automatically:
- SessionEnd captures insights
- 3+ accesses → auto-promote to team
- No manual /remember needed

#### Quick Start

```bash
# 1. Start Qdrant + Ollama
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml up -d
ollama pull qwen3-embedding:0.6b

# 2. Install
/plugin install agentbrain@bms-marketplace

# 3. Use (or let it auto-capture)
/remember "We use PostgreSQL for production"
/recall "database"
```

#### Commands

| Command | Purpose |
|---------|---------|
| `/remember <info>` | Store information |
| `/recall <query>` | Retrieve memories |
| `/forget <topic>` | Delete a memory |
| `/promote <mem> --to <scope>` | Share with team |

---

### honcho-bridge

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
| **Privacy** | Cloud storage | Local only |
| **Features** | Basic memory | Memory hierarchy, search, team sync |

## Quick Start

### AgentBrain (Recommended)

```bash
# 1. Start Qdrant
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml up -d

# 2. Pull embedding model
ollama pull qwen3-embedding:0.6b

# 3. Install plugin
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install agentbrain@bms-marketplace
```

### honcho-bridge

```bash
# 1. Install dependencies
pip install honcho-ai pyyaml python-dotenv

# 2. Start local Honcho (Docker + Ollama)
# See docs/HONCHO_SETUP_GUIDE.md for full setup

# 3. Install plugin
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install honcho-bridge@bms-marketplace
```

## Comparison: AgentBrain vs honcho-bridge

| Feature | AgentBrain | honcho-bridge |
|---------|-----------|---------------|
| **Backend** | Qdrant | Honcho |
| **Embeddings** | Ollama (local) | Ollama (local) |
| **Scoping** | Multi-tenant (user/team/project/org) | Workspace/peer only |
| **Auto-capture** | ✅ Yes | ⚠️ Partial |
| **Auto-promote** | ✅ Yes (3+ accesses) | ❌ No |
| **PR Import** | ✅ Yes | ❌ No |
| **ADR Import** | ✅ Yes | ❌ No |
| **Incident Import** | ✅ Yes | ❌ No |
| **Decay Sweep** | ✅ Yes | ❌ No |
| **Team Sync** | ✅ Repo-based | ⚠️ Manual export/import |

Choose **AgentBrain** for enterprise teams with multi-project environments.
Choose **honcho-bridge** for personal use with Honcho workspaces.

---

## AgentBrain Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "We decided to use Redis for caching"               │
│     ↓                                                       │
│  [Auto-capture] SessionEnd detects pattern                 │
│     ↓                                                       │
│  [Auto-store] /remember "We decided to use Redis..."        │
│     ↓                                                       │
│  [Auto-promote] Team-relevant → team:platform              │
│     ↓                                                       │
│  [PreResponse] Others ask about caching → Auto-inject      │
│                                                             │
│  Result: One person's discovery → Team knowledge           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Tenant Isolation

```
NTT Data (org:ntt-data)
├── Acme Corp (client:acme)
│   └── Alice sees: Acme + platform + org memories
├── GlobalBank (client:globalbank)
│   └── Bob sees: GlobalBank + platform + org memories
└── Platform Team (team:platform)
    └── Everyone sees: Platform conventions
```

### Governance (Anti-Context-Rot)

| Feature | Purpose |
|---------|---------|
| **Health Score** | 0-100 based on age, access, feedback |
| **Decay Sweep** | Deletes memories 90+ days untouched |
| **Access Tracking** | Counts retrievals for promotion |
| **Review Queue** | Shows memories ready for promotion |

---

## honcho-bridge Commands

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

## Configuration

### AgentBrain

```bash
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=agentbrain_memories

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024

# Multi-tenant
AGENTBRAIN_TEAM_ID=platform
AGENTBRAIN_ORG_ID=acme

# Auto-curation
AUTO_PROMOTE_THRESHOLD=3
AGENTBRAIN_AUTO_CAPTURE=true

# Governance
DECAY_STALE_DAYS=60
DECAY_ROT_DAYS=90
```

### honcho-bridge

```bash
# Core Configuration
HONCHO_WORKSPACE=my-project
HONCHO_PEER_ID=user
HONCHO_BASE_URL=http://localhost:8000

# Privacy
HONCHO_PRIVACY_ENABLED=true
HONCHO_REDACT_PATTERNS=email,api_key,password,ip

# Critical Facts (immediate storage)
HONCHO_IMMEDIATE_STORE=true
HONCHO_CRITICAL_PATTERNS=remember:|never forget|important:
```

---

## Project Structure

```
BMsCodingMarket/
├── plugins/
│   ├── agentbrain/                 # Enterprise memory system
│   │   ├── commands/               # /remember, /recall, /forget, /promote
│   │   ├── skills/                 # remember, recall, forget, promote, install
│   │   ├── scripts/
│   │   │   ├── providers/          # Qdrant, Ollama clients
│   │   │   ├── extractors/         # PR, ADR, Incident importers
│   │   │   ├── governance/         # Stats, review queue, decay sweep
│   │   │   ├── query.py            # Semantic search
│   │   │   ├── upsert.py           # Memory storage
│   │   │   └── auto_curation.py    # Auto-promote logic
│   │   ├── hooks/                  # SessionStart, PreResponse, SessionEnd
│   │   ├── agents/                 # Memory curator subagent
│   │   ├── tests/                  # Multi-tenant test suite
│   │   ├── docker/                 # Qdrant compose file
│   │   └── CLAUDE_GUIDE.md         # User guide for Claude Code
│   └── honcho-bridge/              # Honcho local bridge
│       ├── commands/               # Slash commands (10+)
│       ├── skills/                 # Reusable skills (6)
│       ├── scripts/                # Python utilities (14)
│       └── hooks/                  # Event automation (6)
├── docs/
│   ├── AgentBrain/
│   │   ├── PLAN.md                 # Implementation phases
│   │   ├── IDEA.md                 # Original concept
│   │   └── SCENARIO_ANALYSIS.md    # Scenario testing
│   ├── HONCHO_SETUP_GUIDE.md       # Local Honcho setup
│   └── LESSONS_LEARNED.md          # Development insights
├── .env.example                    # Configuration template
└── README.md
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [AgentBrain Plan](docs/AgentBrain/PLAN.md) | Complete implementation plan |
| [AgentBrain Scenarios](docs/AgentBrain/SCENARIO_ANALYSIS.md) | Real-world scenario testing |
| [Honcho Setup Guide](docs/HONCHO_SETUP_GUIDE.md) | Local Honcho setup on Windows |
| [Lessons Learned](docs/LESSONS_LEARNED.md) | Development insights |

---

## Requirements

### AgentBrain
- **Docker Desktop** (for Qdrant)
- **Ollama** — Local embedding server
- **Python 3.10+**
- **Claude Code** — CLI or desktop app

### honcho-bridge
- **Docker Desktop** (for Honcho + PostgreSQL)
- **Ollama** — Local LLM server
- **Python 3.10+**
- **Claude Code** — CLI or desktop app

---

## Links

- [Qdrant](https://qdrant.tech/) — Vector database
- [Ollama](https://ollama.com) — Local LLM runner
- [Honcho](https://github.com/plastic-labs/honcho) — Memory platform

---

## License

MIT

---

**Author:** [Beyhan Meyrali](https://github.com/beyhanmeyrali)
