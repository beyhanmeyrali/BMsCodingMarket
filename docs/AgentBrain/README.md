# AgentBrain

> **Enterprise-grade persistent memory for Claude Code** — Knowledge accumulates automatically, no silos, no manual commands needed.

## Table of Contents

- [Overview](#overview)
- [Why AgentBrain?](#why-agentbrain)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Multi-Tenancy](#multi-tenancy)
- [Auto-Curation](#auto-curation)
- [Governance](#governance)
- [Extractors](#extractors)
- [Hooks](#hooks)
- [API Reference](#api-reference)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Overview

AgentBrain gives Claude Code **persistent memory that accumulates automatically**. Your team's knowledge, decisions, and conventions are captured and shared — invisible to users, no special commands needed.

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| **Invisible** | No `/remember` needed — auto-captures from conversations |
| **Shared** | Auto-promotes valuable insights to team scope |
| **Semantic** | Vector search finds relevant context automatically |
| **Multi-tenant** | Proper isolation between clients, teams, projects |
| **Self-healing** | Decay sweep removes stale memories (anti-context-rot) |

### What It Does

```
Day 1: Alice discovers caching pattern
"We use Redis with 1-hour TTL for sessions"
↓ Auto-captured

Day 5: Bob asks about caching
"How should we handle sessions?"
↓ PreResponse injects Alice's pattern

Day 15: Pattern accessed 3+ times
↓ Auto-promoted to team:platform

Result: Everyone benefits automatically
```

## Why AgentBrain?

### The Problem: Knowledge Silos

1. **Employee silos** - When Alice leaves, her knowledge leaves
2. **Team silos** - Platform team conventions don't reach product teams
3. **Project silos** - Lessons learned in one project repeat in others
4. **Context rot** - Old memories crowd out relevant ones

### The Solution: Automatic Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  KNOWLEDGE ACCUMULATION                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CAPTURE: SessionEnd detects insights                    │
│  2. STORE: Automatic /remember with classification          │
│  3. PROMOTE: 3+ accesses → team scope                       │
│  4. INJECT: PreResponse shows relevant context              │
│  5. DECAY: Sweep removes stale memories                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Comparison

| | AgentBrain | Claude Native | Honcho |
|---|---|---|---|
| **Multi-tenant** | ✅ user/team/project/org | ❌ | ⚠️ workspace/peer |
| **Auto-capture** | ✅ Yes | ❌ No | ⚠️ Partial |
| **Auto-promote** | ✅ Yes (usage-based) | ❌ No | ❌ No |
| **Semantic search** | ✅ Qdrant | ✅ Yes | ✅ Yes |
| **Team sync** | ✅ Repo-based | ❌ No | ⚠️ Manual |
| **PR import** | ✅ Yes | ❌ No | ❌ No |
| **ADR import** | ✅ Yes | ❌ No | ❌ No |
| **Incident import** | ✅ Yes | ❌ No | ❌ No |
| **Decay sweep** | ✅ Yes | ❌ No | ❌ No |
| **100% offline** | ✅ Yes | ❌ No | ✅ Yes |
| **Zero API cost** | ✅ Yes | ❌ No | ✅ Yes |

## Architecture

### Components

```
┌──────────────────────────────────────────────────────────────┐
│                         Claude Code                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ SessionStart│───→│  PreResponse│───→│  SessionEnd │    │
│  │    Hook     │    │    Hook     │    │    Hook     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Sync repo   │    │Query Qdrant │    │Auto-capture │    │
│  │ memories    │    │Inject ctx   │    │insights     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                      AgentBrain Core                          │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │
│  │ Qdrant  │  │ Ollama  │  │Curators │  │ Extractors  │   │
│  │Vector DB│  │Embedder │  │Subagent │  │ PR/ADR/Inc  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Governance Layer                         │  │
│  │  Health Dashboard │ Review Queue │ Decay Sweep       │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐
│ Conversation │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                     SessionEnd Hook                          │
│  1. Detect patterns: "we decided", "team uses", "I prefer"   │
│  2. Extract insight text                                     │
│  3. Classify: user/project/feedback/reference               │
│  4. Store via /remember                                     │
│  5. Promote if team-relevant                                │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Qdrant Storage                           │
│  - Embedding (1024-dim vector via Ollama)                     │
│  - Scope: user:alice, team:platform, etc.                    │
│  - Payload: content, metadata, access_count                  │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    PreResponse Hook                          │
│  1. User asks: "How do we handle caching?"                   │
│  2. Query: "caching" → Qdrant semantic search               │
│  3. Filter by user's allowed scopes                          │
│  4. Inject top 3 results into context                        │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Claude Responds                          │
│  "Based on our team conventions, we use Redis with 1-hour    │
│   TTL for session caching. This was established for the      │
│   payment module and applies across all services."            │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Docker Desktop (for Qdrant)
- Python 3.10+
- Claude Code CLI or Desktop
- Ollama (for embeddings)

### Step 1: Start Qdrant

```bash
# From repository root
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml up -d

# Verify
curl http://localhost:6333/collections
```

### Step 2: Pull Embedding Model

```bash
ollama pull qwen3-embedding:0.6b
```

### Step 3: Install Plugin

```bash
# Add marketplace
/plugin marketplace add beyhanmeyrali/BMsCodingMarket

# Install AgentBrain
/plugin install agentbrain@bms-marketplace
```

### Step 4: Configure (Optional)

Create `.env` in repository root:

```bash
# Multi-tenant (for team environments)
AGENTBRAIN_TEAM_ID=platform
AGENTBRAIN_ORG_ID=acme

# Auto-promotion threshold
AUTO_PROMOTE_THRESHOLD=3

# Decay settings
DECAY_STALE_DAYS=60
DECAY_ROT_DAYS=90
```

### Step 5: Verify

```bash
# Test storage
/remember "Test memory for verification"

# Test retrieval
/recall "test"

# Check governance
python plugins/agentbrain/scripts/governance/memory_stats.py
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | localhost | Qdrant server host |
| `QDRANT_PORT` | 6333 | Qdrant REST API port |
| `QDRANT_COLLECTION` | agentbrain_memories | Collection name |
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama API URL |
| `EMBEDDING_MODEL` | qwen3-embedding:0.6b | Embedding model |
| `EMBEDDING_DIMENSION` | 1024 | Vector dimension |
| `AGENTBRAIN_TEAM_ID` | - | Team name for scoping |
| `AGENTBRAIN_ORG_ID` | - | Organization name |
| `AUTO_PROMOTE_THRESHOLD` | 3 | Accesses before auto-promote |
| `AGENTBRAIN_AUTO_CAPTURE` | true | Enable auto-capture |
| `DECAY_STALE_DAYS` | 60 | Days to consider stale |
| `DECAY_ROT_DAYS` | 90 | Days to consider rot |
| `DECAY_AUTO_DELETE` | false | Auto-delete rot memories |

### Repository Configuration

Create `.agentbrain/config.yml` in your repo:

```yaml
# Team identification
team_id: platform
org_id: acme

# Memory settings
default_scope: team:platform
review_required: false

# Auto-promotion
auto_promote:
  enabled: true
  threshold: 5

# Codeowners for review
codeowners:
  - alice
  - bob
```

## Usage

### Natural Language Triggers (Recommended)

No commands needed! Just use natural language:

```bash
# Explicit storage - works immediately
"Add to AgentBrain: we use PostgreSQL for all new projects"
"Remember that we use Redis for caching"
"Note that API routes use kebab-case"
"Don't forget we never store secrets in code"

# Automatic capture at session end
"We decided to use TypeScript for all new projects"
"The team uses GitHub Actions for CI/CD"
"I prefer tabs over spaces in my code"
```

### Manual Commands

```bash
# Store information
/remember "We use PostgreSQL for all new projects"

# Retrieve memories
/recall "database"

# Forget a memory
/forget "PostgreSQL"

# Promote to team
/promote postgresql_decision --to team:platform
```

### Automatic (Invisible)

No commands needed! AgentBrain:

1. **Captures** insights from conversations (SessionEnd)
2. **Promotes** frequently accessed memories (auto-promote)
3. **Injects** relevant context (PreResponse)

### Examples

#### Example 1: Convention Capture

```
User: "We always use kebab-case for API endpoints"

[SessionEnd auto-captures]

Later: "How should I name this endpoint?"
[PreResponse auto-injects]

Claude: "Based on your conventions, use kebab-case:
        /api/user-profile instead of /api/userProfile"
```

#### Example 2: Decision Sharing

```
Alice (Day 1): "I chose Redis for session caching"
[Stored to user:alice]

Bob (Day 5): "How do we handle sessions?"
[PreResponse finds Alice's memory]
[Access count = 1]

Carol (Day 10): "Session management approach?"
[Access count = 2]

Dave (Day 15): "Caching strategy?"
[Access count = 3 → AUTO-PROMOTE to team:platform]

Everyone now benefits from Alice's discovery
```

#### Example 3: Multi-Tenant Isolation

```
Acme project (Alice):
  /remember "We use Stripe for payments"
  → scope: user:alice (or project:acme-commerce)

GlobalBank project (Bob):
  /remember "We use PayPal for payments"
  → scope:user:bob (or project:gb-mobile)

Alice's /recall "payment" → Returns Stripe only
Bob's /recall "payment" → Returns PayPal only

Both see team:platform memories (conventions, standards)
```

## Multi-Tenancy

### Scope Hierarchy

```
org:acme                           # Widest - entire org
  ├── team:platform                # Platform team members
  │   ├── project:acme-commerce   # Anyone in this repo
  │   │   └── user:alice          # Only Alice
  │   └── user:bob                # Only Bob
  └── client:globalbank
      └── project:gb-mobile
          └── user:carol
```

### Scope Rules

| Scope | Visibility | Example |
|-------|-----------|---------|
| `user:{name}` | Only that user | Personal preferences |
| `team:{name}` | All team members | Conventions, standards |
| `project:{name}` | Repo collaborators | Project decisions |
| `org:{name}` | Entire organization | Policies, compliance |

### Access Control

```python
# Alice's scopes
["user:alice", "team:platform", "project:acme-commerce", "org:acme"]

# Bob's scopes
["user:bob", "team:platform", "project:gb-mobile", "org:acme"]

# Overlap: Both see team:platform and org:acme memories
# Isolation: Alice doesn't see Bob's user memories, vice versa
```

## Auto-Curation

### Auto-Capture Patterns

SessionEnd hook detects these patterns:

| Pattern | Example | Auto-promotes? |
|---------|---------|----------------|
| "we decided" | "We decided to use Redis" | ✅ Yes (team) |
| "we use" | "We use PostgreSQL" | ✅ Yes (team) |
| "team uses" | "Team uses GitHub Actions" | ✅ Yes (team) |
| "I prefer" | "I prefer TypeScript" | ❌ No (personal) |
| "I like" | "I like Neovim" | ❌ No (personal) |

### Auto-Promotion Triggers

```python
# After 3+ accesses, promote to wider scope
user:alice + 3 accesses → team:platform
user:bob + 3 accesses → team:platform

# Configurable
AUTO_PROMOTE_THRESHOLD=5  # Wait for 5 accesses
```

### Access Tracking

Every `/recall` or PreResponse match increments `access_count`:

```python
# Initial storage
memory.access_count = 0
memory.scope = "user:alice"

# After 3 retrievals
memory.access_count = 3
→ Auto-promote to team:platform
```

## Governance

### Health Dashboard

```bash
python scripts/governance/memory_stats.py
```

Output:
```
============================================================
AGENTBRAIN MEMORY HEALTH DASHBOARD
============================================================

Total Memories: 127

--- By Scope ---
  user:alice: 15
  user:bob: 12
  team:platform: 45
  project:acme-commerce: 30
  project:gb-mobile: 25

--- Health Status ---
  High Quality (80+): 98
  Stale (40-60):      20
  ROT RISK (<40):     9

--- SUGGESTED ACTIONS ---
  1. DELETE 9 memories with health < 40 (context rot)
  2. REVIEW 20 stale memories (16% of total)
  3. PROMOTE or DELETE low-value user memories (27 = 21% of total)
```

### Decay Sweep

```bash
# Dry run
python scripts/governance/decay_sweep.py --dry-run

# Actually delete
python scripts/governance/decay_sweep.py --delete

# Custom thresholds
python scripts/governance/decay_sweep.py --stale-days 30 --rot-days 60
```

### Review Queue

```bash
# Show memories ready for promotion
python scripts/governance/review_queue.py

# Auto-promote top 5
python scripts/governance/review_queue.py --auto 5

# Promote specific memory
python scripts/governance/review_queue.py --promote abc123 --to team:platform
```

## Extractors

Import knowledge from existing sources:

### PR Extractor

```bash
# Extract from current PR
python scripts/extractors/pr_extractor.py

# Extract from specific PR
python scripts/extractors/pr_extractor.py 123

# Extract and auto-store
python scripts/extractors/pr_extractor.py 123 --store
```

Extracts:
- Code review comments
- Convention patterns
- "Should/always/never" instructions

### ADR Extractor

```bash
# Find all ADRs in repo
python scripts/extractors/adr_extractor.py --all

# Import specific ADR
python scripts/extractors/adr_extractor.py docs/adr/001-database-choice.md

# Auto-store to team memory
python scripts/extractors/adr_extractor.py --all --store
```

Searches:
- `doc/adr/`
- `docs/adr/`
- `docs/architecture/`
- `docs/decisions/`

### Incident Extractor

```bash
# Import all postmortems
python scripts/extractors/incident_extractor.py --all --store
```

Extracts:
- Root cause
- Lessons learned
- Negative rules ("never do X")
- Action items

## Hooks

### SessionStart

Runs when Claude session starts.

**What it does:**
1. Sync repo-based team memories to Qdrant
2. Regenerate MEMORY.md index
3. Query for relevant context
4. Inject into session

### PreResponse

Runs before each Claude response.

**What it does:**
1. Reads user message
2. Queries Qdrant semantically
3. Filters by user's allowed scopes
4. Injects top 3 relevant memories

**Skips:**
- File operations ("open", "read", "create")
- Commands ("/test", "/run")

### SessionEnd

Runs when session ends.

**What it does:**
1. Analyzes conversation for insights
2. Detects capture patterns
3. Stores valuable insights
4. Promotes team-relevant ones

## API Reference

### Python API

```python
from plugins.agentbrain.scripts.query import query_memories, get_allowed_scopes

# Query memories
results = query_memories(
    query="database preferences",
    scopes=["user:alice", "team:platform"],
    top_k=5,
    min_score=0.7
)

for result in results:
    print(f"{result.memory.file_path}: {result.score}")
```

```python
from plugins.agentbrain.scripts.upsert import upsert_memory

# Store memory
memory_id = upsert_memory(
    file_path="conventions.md",
    scope="team:platform",
    memory_type="reference"
)
```

```python
from plugins.agentbrain.scripts.governance.memory_stats import analyze_memory_health

# Check memory health
analysis = analyze_memory_health(memories)
print(f"Rot candidates: {len(analysis['rot_candidates'])}")
```

### Commands

| Command | Args | Purpose |
|---------|------|---------|
| `/remember <text>` | Text to remember | Store information |
| `/recall <query>` | Search query | Retrieve memories |
| `/forget <topic>` | Topic or name | Delete memory |
| `/promote <name>` | Memory name, --to <scope> | Widen scope |

## Development

### Project Structure

```
plugins/agentbrain/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── agents/
│   └── memory-curator.md        # Curator subagent prompt
├── commands/                    # Slash commands
│   ├── remember.md
│   ├── recall.md
│   ├── forget.md
│   └── promote.md
├── docker/
│   └── qdrant-compose.yml       # Qdrant container
├── hooks/
│   ├── session-start.py         # Session startup
│   ├── preresponse.py           # Pre-response injection
│   ├── session-end-auto-capture.py  # Auto-capture
│   ├── stop.py
│   └── subagent-stop.py
├── scripts/
│   ├── providers/
│   │   ├── qdrant.py            # Vector DB client
│   │   ├── ollama.py            # Embedding client
│   │   └── base.py              # Base classes
│   ├── extractors/
│   │   ├── pr_extractor.py      # PR review import
│   │   ├── adr_extractor.py     # ADR import
│   │   └── incident_extractor.py # Incident import
│   ├── governance/
│   │   ├── memory_stats.py      # Health dashboard
│   │   ├── review_queue.py      # Promotion queue
│   │   └── decay_sweep.py       # Cleanup stale
│   ├── skill_remember.py
│   ├── skill_recall.py
│   ├── skill_forget.py
│   ├── skill_promote.py
│   ├── query.py
│   ├── upsert.py
│   ├── team_config.py
│   ├── regenerate_index.py
│   ├── auto_curation.py         # Auto-promote logic
│   └── utils.py
├── skills/                       # Reusable skills
│   ├── remember/
│   ├── recall/
│   ├── forget/
│   ├── promote/
│   └── install/
├── tests/
│   ├── test_multi_tenant.py     # Isolation tests
│   └── ntt_scenarios.md          # Test scenarios
├── CLAUDE_GUIDE.md              # User guide for Claude Code
├── README.md                    # This file
└── hooks.json                   # Hook configuration
```

### Running Tests

```bash
# Multi-tenant isolation tests
cd plugins/agentbrain
python tests/test_multi_tenant.py

# Expected: 12/12 tests pass
```

### Adding Extractors

Create a new file in `scripts/extractors/`:

```python
"""
My Extractor
"""

from skill_remember import skill_remember

def extract_and_store(source):
    insights = parse(source)
    for insight in insights:
        skill_remember(insight)
```

## Troubleshooting

### Qdrant Connection Failed

```bash
# Check Qdrant is running
curl http://localhost:6333/collections

# Restart Qdrant
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml restart
```

### Ollama Embedding Failed

```bash
# Verify Ollama
ollama list

# Pull model
ollama pull qwen3-embedding:0.6b

# Test embedding
curl http://localhost:11434/api/embeddings -d '{
  "model": "qwen3-embedding:0.6b",
  "prompt": "test"
}'
```

### No Memories Retrieved

1. Check scopes: `python scripts/query.py --scopes`
2. Verify collection: `curl http://localhost:6333/collections/agentbrain_memories`
3. Check embedding dimension matches (1024)

### Auto-Capture Not Working

```bash
# Check environment
echo $AGENTBRAIN_AUTO_CAPTURE  # Should be "true"

# Check SessionEnd hook
cat hooks/hooks.json | grep SessionEnd
```

### Windows Filename Issues

If memories aren't storing, check for invalid characters:

```python
# Filenames are sanitized automatically
# Colons, slashes, etc. replaced with hyphens
```

## License

MIT

---

**Author:** [Beyhan Meyrali](https://github.com/beyhanmeyrali)
