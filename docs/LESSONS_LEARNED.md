# Lessons Learned — BMsCodingMarket

## Honcho Server Does Not Run on Windows

**Date:** 2026-04-13

**Issue:** `ModuleNotFoundError: No module named 'fcntl'` when starting the Honcho FastAPI server on Windows.

`fcntl` is a POSIX-only module (Linux/macOS). Honcho's server code imports it unconditionally in `src/telemetry/reasoning_traces.py`, which is pulled into the full import chain at startup. There is no Windows workaround — the server simply will not start on Windows.

**Impact:** The entire honcho-bridge plugin premise breaks on Windows. The `honcho-ai` Python SDK works fine (it's just HTTP calls), but the server it needs to talk to cannot run on Windows natively.

**Fix options:**
1. Run Honcho server inside WSL2 (Linux subsystem) — works, but adds complexity
2. Run Honcho server inside Docker — the official `docker-compose.yml.example` does this and works on Windows
3. Use the managed cloud service at `api.honcho.dev` — no local server needed, but requires API key

**Recommended approach for this plugin:** Use Docker for the Honcho server, not a bare `git clone + uv run`. The `docker-compose.yml.example` builds the FastAPI server from source (`build: context: .`) so there is no pre-built Docker Hub image — use `docker compose up -d --build`. This handles the Linux dependency transparently. Also note: the compose stack includes Postgres + Redis + the FastAPI `api` service + the `deriver` background worker.

---

## Honcho Postgres Container Credentials

**Date:** 2026-04-13

The Docker container running Postgres was started with non-default credentials:
- User: `honcho`
- Password: `honcho_password`
- Database: `honcho_dev`
- Port: `5433` (host) → `5432` (container)

The README incorrectly documented `postgres/honcho123/honcho_db`. Always `docker inspect <container> --format "{{range .Config.Env}}{{println .}}{{end}}"` to confirm actual credentials before configuring `.env`.

---

## Honcho SDK `peers()` and `sessions()` ARE Iterable

**Date:** 2026-04-13

The `honcho.peers()` and `honcho.sessions()` methods return a `SyncPage` object that auto-paginates when iterated with `for peer in honcho.peers()`. This means a full export IS possible — the earlier stub claiming "official API doesn't expose list endpoints" was wrong. The endpoints exist (`POST /v3/workspaces/{id}/peers/list` etc.) and the SDK wraps them with pagination.

**Correct usage:**
```python
for peer in honcho.peers():          # auto-paginates
    pass

for session in honcho.sessions():    # auto-paginates
    pass

for msg in session.messages():       # auto-paginates
    pass
```

---

## Docker Entrypoint Scripts Get CRLF Line Endings When Cloned on Windows

**Date:** 2026-04-13

When `git clone` runs on Windows without `core.autocrlf=false`, shell scripts (`.sh`) get CRLF line endings. Linux containers then fail with `set: Illegal option -` because `#!/bin/sh` + CRLF = the shell tries to parse `set -e\r` and `\r` is not a valid option flag.

**Fix:** Convert line endings before building the Docker image:
```powershell
$f = "docker\entrypoint.sh"
$c = [System.IO.File]::ReadAllText($f) -replace "`r`n","`n" -replace "`r","`n"
[System.IO.File]::WriteAllText($f, $c, [System.Text.UTF8Encoding]::new($false))
```
Or add a `.gitattributes` entry: `*.sh text eol=lf`

---

## Deriver LLM: Use a No-Thinking Model Variant

**Date:** 2026-04-13

**Issue:** Honcho's deriver hardcodes `reasoning_effort="minimal"` in the LLM call, but for the `custom` (OpenAI-compatible) provider this parameter is silently ignored — it only applies to GPT-5 models (see `src/utils/clients.py` line ~1883). Thinking models like `qwen3.5:9b` therefore run with thinking fully enabled, producing 4096+ token `<think>` blocks that exceed `DERIVER_MAX_OUTPUT_TOKENS` and cause parsing failures.

**Fix:** Use a model that has thinking disabled by default. `qwen3-nothink:latest` (already available locally) works correctly.

**Do NOT** try to create a custom Modelfile with `PARAMETER think false` — Ollama does not accept `think` as a Modelfile parameter. The `think=false` API flag also hangs when used through the OpenAI-compatible `/v1/chat/completions` endpoint. The only reliable solution is a model that doesn't think by default.

---

## Honcho Embedding: Model Name Is Hardcoded, Dimensions Must Match DB

**Date:** 2026-04-13

**Issue 1:** `src/embedding_client.py` line 55 hardcodes `"openai/text-embedding-3-small"` for the `openrouter` provider — not configurable via env. Calling Ollama's `/v1/embeddings` with this model name returns 404.

**Fix:** Added `LLM_EMBEDDING_MODEL` setting to `src/config.py` and updated `embedding_client.py` to use `settings.LLM.EMBEDDING_MODEL or "openai/text-embedding-3-small"`. Set `LLM_EMBEDDING_MODEL=qwen3-embedding:0.6b` in `.env`.

**Issue 2:** `qwen3-embedding:0.6b` returns 1024-dimensional vectors but the pgvector column was created with `Vector(1536)` in migrations. This causes `expected 1536 dimensions, not 1024` on every message insert.

**Fix:** 
1. Added `VECTOR_STORE_DIMENSIONS=1024` to `.env`
2. Changed `Vector(1536)` → `Vector(settings.VECTOR_STORE.DIMENSIONS)` in `src/models.py` (both `message_embeddings` and `documents` tables)
3. Patched the three migration files that also hardcode 1536: `a1b2c3d4e5f6_initial_schema.py`, `917195d9b5e9_add_messageembedding_table.py`, `119a52b73c60_support_external_embeddings.py`
4. Wiped the DB volume (`docker compose down -v`) and rebuilt so migrations run fresh with the correct dimension

**Important:** Changing vector dimensions requires wiping the DB — there is no safe ALTER for pgvector column dimensions.

---

## Deriver Health Check Is a False Alarm

**Date:** 2026-04-13

The `docker-compose.yml` health check for the deriver container tries to connect to `http://localhost:8000/health`. But the deriver is a background worker process — it does not expose an HTTP server on any port. The health check will always fail (`Connection refused`), so the container will always show `unhealthy`. This does not affect functionality. The deriver processes messages correctly regardless of health status.

---

## fastapi-cli Crashes on Windows with Emoji in Terminal Title

**Date:** 2026-04-13

`uv run fastapi dev` crashes on Windows with `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'` because the Windows console cp1252 codec can't render the 🚀 emoji in fastapi-cli's startup banner. Use `uvicorn src.main:app` directly or set `PYTHONIOENCODING=utf-8`. Moot given the `fcntl` blocker, but worth noting for other FastAPI projects.
