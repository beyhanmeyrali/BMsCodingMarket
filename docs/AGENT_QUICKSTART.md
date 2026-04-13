# Honcho Agent Quickstart

> You are an AI agent. Read this first. Full details in `HONCHO_SETUP_GUIDE.md`.

---

## Is the stack running?

```powershell
docker compose ps
```

Expected: `honcho-api-1` is `healthy`. Deriver will show `unhealthy` — that is a false alarm, ignore it.

If nothing is running:

```powershell
cd E:\workspace\honcho
docker compose up -d
```

If you changed source files:

```powershell
docker compose up -d --build
```

---

## SDK — the 5 calls you need

```python
import honcho as h

client = h.Honcho(
    base_url="http://localhost:8000",
    api_key="placeholder",
    workspace_id="your-project-name"   # get-or-create, pick anything consistent
)

peer    = client.peer("alice", metadata={})          # get-or-create user identity
session = client.session("session-001", metadata={}) # get-or-create conversation

# Write
session.add_messages([peer.message("I use TypeScript and deploy on Vercel.")])

# Read (wait ~1 min for deriver to process first)
print(peer.chat("What do you know about this user?"))
# → "Alice uses TypeScript and deploys on Vercel."

# Iterate
for p in client.peers():       # all peers
    for s in p.sessions():     # all sessions for that peer
        for m in s.messages(): # all messages in that session
            print(m.content)
```

---

## What happens after `add_messages()`

```
add_messages() → API embeds message → stored in Postgres
              → work unit pushed to Redis
              → deriver picks it up after ~1 min idle
              → deriver calls qwen3-nothink via Ollama
              → extracts observations → stored in Postgres
              → peer.chat() can now find them
```

If `peer.chat()` returns "I don't have any information" — the deriver hasn't run yet. Wait 1 minute.

---

## Models in use

| Model | Role | Where |
|---|---|---|
| `qwen3-nothink:latest` | Deriver extraction + peer.chat() synthesis | Ollama on host:11434 |
| `qwen3-embedding:0.6b` | Embedding messages and observations (1024-dim) | Ollama on host:11434 |

**Do not switch to a thinking model** (qwen3:8b, qwen3.5:9b etc.) — thinking tokens consume the entire output budget and the deriver extracts zero observations.

---

## Export / Import

```powershell
cd E:\workspace\BMsCodingMarket\plugins\honcho-bridge\scripts

# Export workspace to markdown
python to_wiki.py --base-url http://localhost:8000 --workspace your-project-name --output wiki/

# Import markdown back
python wiki_to_honcho.py --base-url http://localhost:8000 --workspace your-project-name --wiki wiki/
```

---

## Troubleshooting in 30 seconds

| Symptom | Fix |
|---|---|
| `peer.chat()` → "I don't have any information" | Wait 1 min for deriver; check `docker compose logs deriver --tail 20` |
| `Observation Count: 0` in deriver logs | Thinking model — switch to `qwen3-nothink:latest` |
| `ServerError` on `add_messages()` | Check `docker compose logs api --tail 20` — likely embedding error |
| `expected 1536 dimensions, not 1024` | `docker compose down -v && docker compose up -d --build` |
| `model "openai/text-embedding-3-small" not found` | Source patch not applied — see `HONCHO_SETUP_GUIDE.md` Step 2 |
| Containers not starting | `docker compose logs` — check for CRLF in entrypoint.sh |

---

## Key file locations

```
E:\workspace\honcho\          ← Honcho server (Docker build source)
  .env                        ← all config lives here
  docker-compose.yml

E:\workspace\BMsCodingMarket\
  docs\HONCHO_SETUP_GUIDE.md  ← full setup guide with all patches
  docs\LESSONS_LEARNED.md     ← every failure we hit and how we fixed it
  plugins\honcho-bridge\scripts\
    to_wiki.py
    wiki_to_honcho.py
```
