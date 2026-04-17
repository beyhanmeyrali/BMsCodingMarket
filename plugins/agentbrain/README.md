# AgentBrain

Enterprise-grade persistent memory system for Claude Code with semantic retrieval, multi-tenant scoping, and auto-curation.

## Features

- **Persistent memory** — Sessions end, learnings remain
- **Shared knowledge** — Team and project-level memory layers
- **Semantic retrieval** — Vector DB finds relevant memories automatically
- **Multi-tenant** — User, team, project, and org scopes with isolation
- **100% self-hosted** — Your data, your infra, free/OSS tools only

## Architecture

```
Session → AgentBrain → Qdrant (Vector DB) + Ollama (Embeddings)
                      ↓
                 Scoped Retrieval
                 (user/team/project/org)
```

## Quick Start

### 1. Start Qdrant

```bash
docker-compose -f ~/.claude/plugins/agentbrain/docker/qdrant-compose.yml up -d
```

### 2. Start Ollama

```bash
ollama serve
ollama pull qwen3:0.6b
```

### 3. Configure Environment

```bash
cp ~/.claude/plugins/agentbrain/.env.example ~/.agentbrain.env
# Edit ~/.agentbrain.env with your settings
```

### 4. Install Plugin

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install agentbrain@bms-marketplace
```

### 5. Seed Existing Memories (Optional)

```bash
python ~/.claude/plugins/agentbrain/scripts/seed_memories.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | localhost | Qdrant server host |
| `QDRANT_PORT` | 6333 | Qdrant REST API port |
| `EMBEDDING_MODEL` | qwen3:0.6b | Ollama embedding model |
| `MEMORY_DIR` | ~/.claude/memory | Memory storage directory |
| `RETRIEVAL_TOP_K` | 8 | Max memories to retrieve |

## Memory Scopes

```
user:bob          # Personal memories, only Bob sees
team:platform     # Platform team conventions, team members see
project:acme/api  # API project decisions, anyone working in repo sees
org:acme          # Company-wide policies, everyone sees
```

## Trust Metadata

Every memory includes governance metadata for enterprise use:

| Field | Type | Description |
|-------|------|-------------|
| `source_type` | string | Where memory came from: `manual`, `pr`, `adr`, `incident`, `conversation`, `auto_captured` |
| `approval_status` | string | `draft`, `approved`, `archived`, `superseded` |
| `confidence` | float | 0.0-1.0 score indicating reliability |
| `last_validated` | timestamp | When memory was last reviewed/validated |
| `owner` | string | Team or individual responsible |
| `supersedes` | string | ID of memory this replaces |
| `superseded_by` | string | ID of newer memory that replaces this |

### Memory Frontmatter Example

```yaml
---
name: API Authentication Decision
description: How we handle auth in our APIs
type: project
scope: project:myapi
# Trust Metadata
source_type: adr
approval_status: approved
confidence: 0.9
owner: platform-team
domain_tags:
  - security
  - jwt
  - oauth2
---
```

## Domain Tagging

Memories can be tagged with technical domains for precise filtering:

**Common SAP Tags:**
- `RAP` - RESTful Application Programming
- `CDS` - Core Data Services
- `ABAP_Cloud` - ABAP Cloud development
- `Transport` - Transport requests
- `ATC` - ABAP Test Cockpit
- `Clean_Core` - Clean Core methodology
- `BTP` - SAP Business Technology Platform

**Usage in Memory Files:**
```yaml
domain_tags:
  - RAP
  - CDS
  - OData
```

## Retrieval Modes

Query memories by type using retrieval modes:

| Mode | Description | Best For |
|------|-------------|----------|
| `similar_incidents` | Related incidents | Troubleshooting, root cause analysis |
| `conventions` | Team conventions | Onboarding, consistency |
| `approved_standards` | Approved standards | Critical decisions, compliance |
| `example_solutions` | Working solutions | Learning, reference implementations |
| `architecture_decisions` | ADRs | Understanding tradeoffs |

**Usage:**
```
/recall "RAP handler error" --mode similar_incidents --domain-tags RAP
/recall "naming conventions" --mode conventions
/recall "auth patterns" --mode approved_standards
```

## Scripts

| Script | Purpose | Options |
|--------|---------|--------|
| `seed_memories.py` | Import existing memories into vector DB | `--scope`, `--type` |
| `query.py` | Semantic search with scope filtering | `--mode`, `--domain-tags`, `--top-k` |
| `embed.py` | Generate embeddings via Ollama | `--model` |
| `upsert.py` | Write/update memories in vector DB | `--domain-tags`, `--source-type`, `--approval-status`, `--confidence`, `--owner` |
| `regenerate_index.py` | Generate MEMORY.md from memory files | `--output` |

## Hooks

| Hook | Purpose |
|------|---------|
| SessionStart | Regenerate index + query + inject context |

## Status

**Phase 0 MVP** — Core retrieval with Qdrant + Ollama embeddings.

Coming in Phase 1:
- Auto-curation via subagents
- Stop/SubagentStop hooks
- User-facing skills: `/recall`, `/remember`, `/forget`

## License

MIT
