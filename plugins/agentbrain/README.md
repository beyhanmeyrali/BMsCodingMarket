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

## Scripts

| Script | Purpose |
|--------|---------|
| `seed_memories.py` | Import existing memories into vector DB |
| `query.py` | Semantic search with scope filtering |
| `embed.py` | Generate embeddings via Ollama |
| `upsert.py` | Write/update memories in vector DB |
| `regenerate_index.py` | Generate MEMORY.md from memory files |

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
