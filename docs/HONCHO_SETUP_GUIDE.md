# Honcho Setup Guide — Local, Fully Offline on Windows

> **For agents:** This document is self-contained. Follow it top-to-bottom and you will have a working Honcho memory stack running locally with no cloud API keys.

---

## Why Use Honcho?

Without a memory layer, every conversation with an AI agent starts from zero. The agent has no knowledge of who you are, what you've worked on, your preferences, or past decisions. You repeat context every session. Across thousands of interactions this is a significant friction.

Honcho solves this. It is a **user-modeling memory platform** purpose-built for AI agents. It provides:

- **Persistent peer memory** — facts about each user are extracted automatically from conversations and stored durably
- **Semantic retrieval** — `peer.chat("what do you know about this user?")` queries the memory graph using vector similarity, not keyword matching
- **Automatic observation extraction** — a background worker (the *deriver*) reads new messages, calls an LLM, and writes structured observations like `"user's name is Bob"`, `"user works at a fintech startup"` without any application code
- **Multi-session awareness** — observations from session 1 are available in session 100
- **Export/import** — full round-trip to markdown wiki format for backup, diffing, and portability

Honcho's abstraction:

```
Workspace  →  Peer (a user identity)
               ├─ Sessions (conversation threads)
               │   └─ Messages
               └─ Observations (extracted facts, searchable by vector)
```

`peer.chat(query)` is the primary query interface. It spins up an agent that searches observations by vector similarity and synthesizes a grounded answer.

---

## Architecture of This Setup

```mermaid
graph TD
    subgraph Host["Windows Host"]
        Ollama["Ollama\n(inference server)\nport 11434"]
        SDK["honcho-ai SDK\n(Python, pip installed)"]
        Scripts["to_wiki.py / wiki_to_honcho.py\n(export/import scripts)"]
    end

    subgraph Docker["Docker (Linux containers)"]
        API["honcho-api\n(FastAPI, port 8000)"]
        Deriver["honcho-deriver\n(background worker)"]
        Postgres["postgres + pgvector\n(port 5432)"]
        Redis["redis\n(port 6379)"]
    end

    subgraph Ollama_Models["Ollama Models"]
        NothinkModel["qwen3-nothink:latest\n(deriver LLM + dialectic)"]
        EmbedModel["qwen3-embedding:0.6b\n(1024-dim embeddings)"]
    end

    SDK -->|"HTTP POST /v3/..."| API
    Scripts -->|"HTTP POST /v3/..."| API
    API --> Postgres
    API --> Redis
    Deriver --> Postgres
    Deriver --> Redis
    Deriver -->|"OpenAI-compat\nPOST /v1/chat/completions"| Ollama
    API -->|"OpenAI-compat\nPOST /v1/embeddings"| Ollama
    Ollama --> NothinkModel
    Ollama --> EmbedModel
```

### Why Docker for the server?

Honcho's FastAPI server uses `fcntl` — a POSIX-only Python module. It cannot start natively on Windows. Docker runs it in a Linux container, which works on all platforms. There is no pre-built Docker Hub image; the compose file builds from source.

### Why Ollama?

Ollama is a local inference server with an OpenAI-compatible API (`/v1/chat/completions`, `/v1/embeddings`). It manages model loading, GPU offloading, and context windowing. Honcho's `custom` LLM provider setting points directly at Ollama's endpoint.

---

## Prerequisites

- **Docker Desktop** (with Linux containers mode)
- **Git**
- **Python 3.10+** with `pip`
- **Ollama** — download from https://ollama.com

Install the required Ollama models:

```powershell
ollama pull qwen3-nothink:latest
ollama pull qwen3-embedding:0.6b
```

`qwen3-nothink` is Qwen3 8B with thinking disabled at the model level. This is critical — see the [No-Thinking Requirement](#no-thinking-requirement) section.

---

## Step 1 — Clone Honcho Server

```powershell
git clone https://github.com/plastic-labs/honcho.git E:\workspace\honcho
cd E:\workspace\honcho
```

### Fix CRLF line endings (Windows-specific, mandatory)

When `git clone` runs on Windows, shell scripts get Windows (`\r\n`) line endings. The Docker container runs Linux, which chokes on `\r` with `set: Illegal option -`.

```powershell
$f = "docker\entrypoint.sh"
$c = [System.IO.File]::ReadAllText($f) -replace "`r`n","`n" -replace "`r","`n"
[System.IO.File]::WriteAllText($f, $c, [System.Text.UTF8Encoding]::new($false))
```

Or permanently prevent this by adding to `.gitattributes`:
```
*.sh text eol=lf
```

---

## Step 2 — Patch the Source (Required for Local Ollama)

Honcho was designed for cloud providers. Two source files need patching to work with a local Ollama embedding model.

### Patch 1 — Make embedding model configurable (`src/embedding_client.py`)

Line 55 hardcodes `"openai/text-embedding-3-small"` for the `openrouter` provider. Replace it so it reads from config:

```python
# Before (line 55):
self.model = "openai/text-embedding-3-small"

# After:
self.model = settings.LLM.EMBEDDING_MODEL or "openai/text-embedding-3-small"
```

### Patch 2 — Add `EMBEDDING_MODEL` setting (`src/config.py`)

Find the `EMBEDDING_PROVIDER` line (around line 216) and add the new setting below it:

```python
EMBEDDING_PROVIDER: Literal["openai", "gemini", "openrouter"] = "openai"
EMBEDDING_MODEL: str | None = None   # add this line
```

### Patch 3 — Make vector dimensions configurable (`src/models.py`)

Add import at top of file:

```python
from src.config import settings
```

Find both `Vector(1536)` occurrences and replace:

```python
# Both message_embeddings and documents tables:
embedding: MappedColumn[Any] = mapped_column(Vector(settings.VECTOR_STORE.DIMENSIONS), nullable=True)
```

### Patch 4 — Fix migration files

Three migration files also hardcode `1536`. Add `from src.config import settings` to their imports and replace `Vector(1536)` with `Vector(settings.VECTOR_STORE.DIMENSIONS)` in:

- `migrations/versions/a1b2c3d4e5f6_initial_schema.py` (line ~366)
- `migrations/versions/917195d9b5e9_add_messageembedding_table.py` (line ~31)
- `migrations/versions/119a52b73c60_support_external_embeddings.py` (lines ~45, ~53 — these use `existing_type=` so they are tracking only, but patch for consistency)

---

## Step 3 — Configure `.env`

```powershell
cp .env.example .env   # or copy docker-compose.yml.example → docker-compose.yml
```

Paste this working configuration into `.env` (replace/uncomment existing lines):

```bash
# =============================================================================
# Database (internal Docker network — use service name, not localhost)
# =============================================================================
DB_CONNECTION_URI=postgresql+psycopg://honcho:honcho_password@database:5432/honcho_dev

# =============================================================================
# Auth (disable for local dev)
# =============================================================================
AUTH_USE_AUTH=false

# =============================================================================
# LLM — Ollama on the host machine
# host.docker.internal resolves to the Windows host IP from inside Docker
# =============================================================================
LLM_OPENAI_COMPATIBLE_BASE_URL=http://host.docker.internal:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=sk-placeholder

# =============================================================================
# Embedding — use local Ollama model
# =============================================================================
LLM_EMBEDDING_PROVIDER=openrouter
LLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBED_MESSAGES=true

# =============================================================================
# Vector store dimensions — must match your embedding model's output
# qwen3-embedding:0.6b → 1024 dims
# openai/text-embedding-3-small → 1536 dims
# =============================================================================
VECTOR_STORE_DIMENSIONS=1024

# =============================================================================
# Deriver (background observation extractor)
# =============================================================================
DERIVER_ENABLED=true
DERIVER_PROVIDER=custom
DERIVER_MODEL=qwen3-nothink:latest
DERIVER_MAX_OUTPUT_TOKENS=4096
DERIVER_STALE_SESSION_TIMEOUT_MINUTES=1
DERIVER_LOG_OBSERVATIONS=true
DERIVER_FLUSH_ENABLED=true

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL=INFO
```

---

## Step 4 — Copy and Build Docker Compose

```powershell
cp docker-compose.yml.example docker-compose.yml
docker compose up -d --build
```

`--build` is required because there is no pre-built image — the compose file builds the FastAPI server and deriver from source. Subsequent restarts can use `docker compose up -d` (no `--build`) unless source files changed.

### Verify all containers are up

```powershell
docker compose ps
```

Expected output:

```
NAME                 STATUS
honcho-api-1         Up (healthy)
honcho-database-1    Up (healthy)
honcho-redis-1       Up (healthy)
honcho-deriver-1     Up (unhealthy)   ← false alarm, see note below
```

> **Note on deriver `unhealthy`:** The Docker health check for the deriver container tries to connect to `http://localhost:8000/health`. The deriver is a background worker — it does not expose an HTTP server on any port. The health check will always fail. This is a bug in the upstream `docker-compose.yml`. The deriver is functioning correctly regardless of this status.

---

## Step 5 — Install the SDK and Test

```powershell
pip install honcho-ai
```

Run a quick end-to-end test:

```python
import honcho as h

client = h.Honcho(
    base_url="http://localhost:8000",
    api_key="placeholder",
    workspace_id="my-project"
)

peer = client.peer("alice", metadata={})
session = client.session("session-001", metadata={})

session.add_messages([
    peer.message("My name is Alice and I specialize in distributed systems.")
])
print("Message stored.")
```

Wait ~1 minute for the deriver to process (it polls every `DERIVER_STALE_SESSION_TIMEOUT_MINUTES`), then query:

```python
response = peer.chat("What do you know about this user?")
print(response)
# → "The user is Alice. She specializes in distributed systems."
```

---

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant App as Your App / Script
    participant API as honcho-api (Docker)
    participant PG as Postgres + pgvector
    participant Redis
    participant Deriver as honcho-deriver (Docker)
    participant Ollama as Ollama (Host)

    App->>API: POST /v3/workspaces/{ws}/sessions/{s}/messages
    API->>Ollama: POST /v1/embeddings (qwen3-embedding:0.6b)
    Ollama-->>API: 1024-dim vector
    API->>PG: INSERT message + embedding
    API->>Redis: enqueue deriver work unit

    Note over Deriver: polls Redis every ~1 min
    Deriver->>Redis: claim work unit
    Deriver->>PG: fetch messages for session
    Deriver->>Ollama: POST /v1/chat/completions (qwen3-nothink:latest)
    Ollama-->>Deriver: JSON observations list
    Deriver->>PG: INSERT observations (with embeddings)

    App->>API: peer.chat("what do you know about alice?")
    API->>Ollama: POST /v1/embeddings (embed query)
    Ollama-->>API: 1024-dim query vector
    API->>PG: vector similarity search on observations
    PG-->>API: top-k matching observations
    API->>Ollama: POST /v1/chat/completions (synthesize answer)
    Ollama-->>API: grounded answer
    API-->>App: "Alice specializes in distributed systems."
```

---

## No-Thinking Requirement

This is the most important non-obvious pitfall.

### The problem

Honcho's deriver calls the LLM with `reasoning_effort="minimal"`. This is an Anthropic/OpenAI concept for suppressing extended reasoning. For Honcho's `custom` provider (OpenAI-compatible, i.e. Ollama), **this parameter is silently ignored** — the code only applies it when the model name contains `"gpt-5"` (see `src/utils/clients.py`).

If you use a thinking model like `qwen3:8b` or `qwen3.5:9b`:

1. The model enters a `<think>...</think>` block before answering
2. These thinking tokens count against `DERIVER_MAX_OUTPUT_TOKENS`
3. The model hits the token limit mid-think, before writing any actual output
4. The deriver gets an empty response → zero observations extracted → no memory stored

### Attempted fixes that don't work

| Approach | Why it fails |
|---|---|
| `PARAMETER think false` in Ollama Modelfile | Ollama does not accept `think` as a Modelfile parameter |
| `"think": false` in POST body to `/v1/chat/completions` | Hangs indefinitely — Ollama bug with this flag via OpenAI-compat endpoint |
| Raising `DERIVER_MAX_OUTPUT_TOKENS` very high | Model still runs full thinking budget before answering; doesn't help |

### The correct fix

Use a model that has thinking **disabled at the model level**. Ollama provides `qwen3-nothink` variants that are the same weights but with the thinking system prompt removed.

```powershell
ollama pull qwen3-nothink:latest   # 5.2 GB, Qwen3 8B, no thinking
```

Then in `.env`:
```bash
DERIVER_MODEL=qwen3-nothink:latest
```

Same applies to dialectic, summary, and dream models — set all of them to `qwen3-nothink:latest` if you are using Qwen3-family models through Ollama.

---

## Embedding Dimensions

Every embedding model outputs a fixed number of dimensions. The pgvector column in Postgres must be created with the same number. **You cannot ALTER a pgvector column to change dimensions** — the column must be dropped and recreated.

| Model | Dimensions |
|---|---|
| `openai/text-embedding-3-small` (OpenAI cloud) | 1536 |
| `qwen3-embedding:0.6b` (Ollama local) | 1024 |
| `text-embedding-ada-002` (OpenAI cloud) | 1536 |

Honcho defaults to 1536 (for OpenAI). When using `qwen3-embedding:0.6b` you must set:

```bash
VECTOR_STORE_DIMENSIONS=1024
```

And apply the source patches in Step 2. If you change dimensions after the DB was already initialized, wipe the volume:

```powershell
docker compose down -v   # destroys all data
docker compose up -d --build
```

---

## Rebuilding vs Restarting

| Situation | Command |
|---|---|
| Changed `.env` only | `docker compose down && docker compose up -d` |
| Changed any `src/` Python file or migration | `docker compose down && docker compose up -d --build` |
| Changed embedding dimensions (requires DB wipe) | `docker compose down -v && docker compose up -d --build` |

---

## SDK Quick Reference

```python
import honcho as h

client = h.Honcho(
    base_url="http://localhost:8000",
    api_key="placeholder",      # ignored when AUTH_USE_AUTH=false
    workspace_id="my-project"
)

# Get or create a peer (user identity)
peer = client.peer("alice", metadata={"role": "engineer"})

# Get or create a session (conversation thread)
session = client.session("session-42", metadata={})

# Add messages (triggers embedding + deriver queue)
session.add_messages([
    peer.message("I prefer concise responses and use vim."),
])

# Query memory (vector search + LLM synthesis)
response = peer.chat("What are this user's preferences?")

# Iterate all peers (auto-paginating)
for peer in client.peers():
    print(peer.id)

# Iterate sessions for a peer
for session in peer.sessions():
    print(session.id)

# Iterate messages in a session
for msg in session.messages():
    print(msg.content)
```

---

## Troubleshooting

### `set: Illegal option -` during Docker build

Shell script has CRLF line endings. Fix: see Step 1 CRLF section.

### `model "openai/text-embedding-3-small" not found`

You haven't applied the source patch to `embedding_client.py` or `LLM_EMBEDDING_MODEL` is not set in `.env`.

### `expected 1536 dimensions, not 1024`

`VECTOR_STORE_DIMENSIONS` is not set, or the migrations ran with the old hardcoded 1536 before patching. Wipe the DB volume and rebuild.

### Deriver extracts zero observations

Almost certainly a thinking model issue. Check deriver logs:

```powershell
docker compose logs deriver --tail 50
```

Look for `finish_reason: length` in debug output — this means the model hit the token limit in the thinking block. Switch to `qwen3-nothink:latest`.

### `peer.chat()` returns "I don't have any information"

Either:
1. The deriver hasn't run yet — wait 1 minute (or reduce `DERIVER_STALE_SESSION_TIMEOUT_MINUTES=1`)
2. Embeddings are failing — check API logs for embedding errors
3. Vector dimensions mismatch — observations stored with wrong dimension vector

### Deriver shows `unhealthy` in `docker compose ps`

Expected and harmless. See the note in Step 4.

### `honcho.http.exceptions.ServerError: An unexpected error occurred`

Check API logs immediately:

```powershell
docker compose logs api --tail 30
```

Most common cause: embedding dimension mismatch (`expected 1536 dimensions, not 1024`).

---

## File Reference

```
E:\workspace\honcho\               ← cloned Honcho server repo
├── .env                           ← your configuration (not committed)
├── docker-compose.yml             ← copied from docker-compose.yml.example
├── docker/entrypoint.sh           ← must have LF line endings
└── src/
    ├── config.py                  ← add EMBEDDING_MODEL field here
    ├── embedding_client.py        ← patch line 55 to read from settings
    ├── models.py                  ← patch Vector(1536) → Vector(settings...)
    └── deriver/deriver.py         ← FYI: reasoning_effort hardcoded line 137

E:\workspace\BMsCodingMarket\
└── plugins\honcho-bridge\
    └── scripts\
        ├── to_wiki.py             ← export workspace to markdown
        └── wiki_to_honcho.py     ← import markdown back to Honcho
```
