# Honcho Bridge — Implementation Notes

## Architecture

The plugin is a thin bridge between Claude Code and the official Honcho memory platform. It provides:

1. **Skills** — teach Claude Code how to use Honcho locally
2. **Commands** — install/export/import workflows
3. **Scripts** — `to_wiki.py` and `wiki_to_honcho.py` for wiki round-tripping

### Stack

| Component | Role | Where it runs |
|-----------|------|---------------|
| `honcho-ai` SDK | Python client, makes HTTP calls to Honcho server | Host (pip install) |
| Honcho FastAPI server | REST API for memory storage/retrieval | Docker (`honcho-api-1`) |
| Postgres + pgvector | Persistent storage | Docker (`honcho-database-1`) |
| Redis | Caching layer | Docker (`honcho-redis-1`) |
| Ollama + qwen3-nothink:latest | Local LLM for deriver, dialectic, peer.chat() | Host (ollama serve) |
| Ollama + qwen3-embedding:0.6b | Embedding messages and observations (1024-dim) | Host (ollama serve) |

### Why Docker for the server?

Honcho's server uses `fcntl` (POSIX-only) and cannot run natively on Windows. Docker builds and runs it in a Linux container transparently on all platforms.

---

## Scripts

### `to_wiki.py`

Exports all peers and sessions from a Honcho workspace to markdown files.

**How it works:**
- Iterates `honcho.peers()` (auto-paginating `SyncPage`)
- Iterates `honcho.sessions()` (auto-paginating `SyncPage`)
- For each session iterates `session.messages()` (auto-paginating)
- Writes `wiki/peers/<id>.md`, `wiki/sessions/<id>.md`, `wiki/index.md`

**Usage:**
```bash
python to_wiki.py --base-url http://localhost:8000 --workspace <id> --output wiki/
```

### `wiki_to_honcho.py`

Imports peer and session markdown files back into Honcho.

**How it works:**
- Reads YAML frontmatter from each peer file → calls `honcho.peer(id, metadata={...})`
- Reads YAML frontmatter + transcript section from each session file
- Parses transcript (stateful line parser — `**Name**:` header followed by content lines)
- Calls `peer.message(content)` for each line then `session.add_messages([...])`

**Usage:**
```bash
python wiki_to_honcho.py --base-url http://localhost:8000 --workspace <id> --wiki wiki/
```

---

## Transcript Format

Export writes (and import expects) this format in session markdown:

```markdown
## Transcript

### 2026-04-13 11:02

**Alice**:

Hey Bob, what is the capital of France?

### 2026-04-13 11:02

**Bob**:

The capital of France is Paris.
```

The import parser is stateful: `### timestamp` resets current speaker, `**Name**:` sets current speaker, subsequent non-empty lines are accumulated as message content, flushed on the next speaker or `## ` section header.

---

## Known Limitations

- **No `peer.chat()` without LLM** — basic storage/retrieval works without LLM config, but `peer.chat()`, `session.context()` and the deriver all require a working LLM endpoint. Set `DERIVER_ENABLED=false` etc. to run without LLM.
- **Session IDs are user-managed** — Honcho uses get-or-create semantics; importing the same session twice appends messages rather than replacing them.
- **`session_count` on peer pages** — counts sessions where the peer has messages; can be inflated if the same peer object is created multiple times via `honcho.peer()`.

---

## .env Working Config (Docker Compose)

> Full config with all options documented in `docs/HONCHO_SETUP_GUIDE.md`.

```bash
DB_CONNECTION_URI=postgresql+psycopg://honcho:honcho_password@database:5432/honcho_dev
AUTH_USE_AUTH=false
LLM_OPENAI_COMPATIBLE_BASE_URL=http://host.docker.internal:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=sk-placeholder
LLM_EMBEDDING_PROVIDER=openrouter
LLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBED_MESSAGES=true
VECTOR_STORE_DIMENSIONS=1024
DERIVER_ENABLED=true
DERIVER_PROVIDER=custom
DERIVER_MODEL=qwen3-nothink:latest
DERIVER_MAX_OUTPUT_TOKENS=4096
DERIVER_STALE_SESSION_TIMEOUT_MINUTES=1
DERIVER_FLUSH_ENABLED=true
```
