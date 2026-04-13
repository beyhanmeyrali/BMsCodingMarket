---
name: honcho-install
description: Install official Honcho memory system with Ollama locally. Sets up Postgres database, Honcho server (via Docker), and Ollama for 100% local AI agent memory.
---

# Honcho + Ollama Local Installation

This command installs the official Honcho memory system with Ollama for 100% local AI agent memory.

> **Windows users:** The Honcho server must run via Docker — it uses Linux-only system calls (`fcntl`) and cannot run natively on Windows. The Docker approach works on all platforms.

## What Gets Installed

1. **Ollama** - Local LLM runner (qwen3.5:9b for chat, qwen3-embedding for search)
2. **PostgreSQL + pgvector** - Database for Honcho storage (via Docker)
3. **Honcho server** - Official FastAPI memory service (via Docker)
4. **Honcho SDK** - Python client (`honcho-ai`)

## Quick Install

```bash
# 1. Install Ollama and pull models
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:9b
ollama pull qwen3-embedding:0.6b
ollama serve &

# 2. Install Honcho SDK
pip install honcho-ai pyyaml

# 3. Clone Honcho and start via Docker Compose (works on Windows/Mac/Linux)
git clone https://github.com/plastic-labs/honcho.git
cd honcho
cp .env.template .env
cp docker-compose.yml.example docker-compose.yml
```

Edit `.env` with these minimal settings:
```bash
DB_CONNECTION_URI=postgresql+psycopg://honcho:honcho_password@database:5432/honcho_dev
LLM_OPENAI_COMPATIBLE_BASE_URL=http://host.docker.internal:11434/v1
LLM_OPENAI_COMPATIBLE_API_KEY=sk-placeholder
EMBED_MESSAGES=false
DERIVER_ENABLED=false
SUMMARY_ENABLED=false
DREAM_ENABLED=false
AUTH_USE_AUTH=false
```

```bash
# 4. Build and start the full stack (Postgres + Redis + Honcho FastAPI server)
# --build is required on first run — there's no pre-built image, it builds from source
docker compose up -d --build

# Server starts at http://localhost:8000
```

## Verify Installation

```bash
curl http://localhost:8000/health
```

```python
from honcho import Honcho

honcho = Honcho(base_url="http://localhost:8000", workspace_id="test")
user = honcho.peer("test-user")
print(f"Created peer: {user.id}")
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Your App   │────▶│   Honcho    │────▶│  Postgres   │
│             │     │  (Docker)   │     │  (Docker)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Ollama    │
                    │ (local)     │
                    └─────────────┘
```

## Step 5: Wire Up Auto-Memory Hooks

After verifying the server is running, set up the opencode plugin hooks so the agent **automatically stores session summaries to Honcho** when it finishes each turn.

Create `.opencode/plugins/honcho-memory.ts` in the project root:

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import * as path from "path"

const SCRIPTS_DIR = path.resolve(
  import.meta.dirname,
  "../../plugins/honcho-bridge/scripts"
)

async function storeToHoncho($: any, sessionId: string, summary: string) {
  const script = path.join(SCRIPTS_DIR, "store_to_honcho.py")
  const escaped = summary.replace(/'/g, "'\\''")
  try {
    await $`python "${script}" --session-id "${sessionId}" --summary "${escaped}"`
  } catch (err) {
    console.error("[honcho-memory] Failed to store:", err)
  }
}

export const HonchoMemoryPlugin: Plugin = async ({ client, $ }) => {
  const storedSessions = new Set<string>()

  return {
    "experimental.session.compacting": async (input, output) => {
      const sessionId: string = (input as any).session?.id ?? "unknown"
      storedSessions.add(`compact:${sessionId}`)
      const summary = output.prompt
        ? `[Compaction] ${output.prompt.slice(0, 2000)}`
        : `[Session compacted: ${sessionId}]`
      await storeToHoncho($, sessionId, summary)
    },

    "session.idle": async ({ event }: any) => {
      const sessionId: string = event?.properties?.id ?? "unknown"
      if (storedSessions.has(`compact:${sessionId}`)) return

      const messages = await client.session.messages({ path: { id: sessionId } })
      const recent = (messages.data ?? []).slice(-6)
      const lines: string[] = []
      for (const m of recent) {
        for (const part of m.parts ?? []) {
          if ((part as any).type === "text" && (part as any).text?.trim()) {
            const role = m.info?.role === "assistant" ? "Agent" : "User"
            lines.push(`${role}: ${(part as any).text.trim().slice(0, 500)}`)
          }
        }
      }
      if (lines.length === 0) return
      await storeToHoncho($, sessionId, `[Session ${sessionId}]\n${lines.join("\n")}`)
      storedSessions.add(`idle:${sessionId}`)
    },
  }
}
```

Also create `.opencode/package.json` so opencode installs the plugin type dependency:

```json
{
  "dependencies": {
    "@opencode-ai/plugin": "latest"
  }
}
```

Verify the hook script works:

```bash
python plugins/honcho-bridge/scripts/store_to_honcho.py \
  --session-id test-001 \
  --summary "Hook test successful"
# → [honcho-memory] Stored summary for session opencode-test-001
```

From this point on, every time the agent finishes a turn, the session content is stored to Honcho and becomes queryable via `peer.chat()` in future sessions.

## Next Steps

- Use `/honcho-export` to export memory to wiki format
- Use `/honcho-import` to import wiki knowledge into Honcho
