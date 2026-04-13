---
name: honcho-store
description: Store messages and conversations to Honcho memory. Use when you want to capture important information, decisions, or context that should be remembered in future sessions.
---

# Honcho Memory Store

Store messages to Honcho memory so they can be learned and recalled later.

## Usage

```bash
python plugins/honcho-bridge/scripts/honcho_store.py \
  --base-url http://localhost:8000 \
  --workspace <workspace-id> \
  --peer <peer-id> \
  --session <session-id> \
  --message "<content to store>"
```

## Examples

```bash
# Store a user preference
python plugins/honcho-bridge/scripts/honcho_store.py \
  --workspace my-project --peer alice --session session-001 \
  --message "I prefer TypeScript over JavaScript for new projects."

# Store a technical decision
python plugins/honcho-bridge/scripts/honcho_store.py \
  --workspace my-project --peer alice --session decisions \
  --message "We chose PostgreSQL over MySQL for JSONB support."

# Store multiple messages
python plugins/honcho-bridge/scripts/honcho_store.py \
  --workspace my-project --peer alice --session session-001 \
  --message "First message" \
  --message "Second message" \
  --message "Third message"
```

## How it works

1. Creates peer if they don't exist
2. Creates session if it doesn't exist
3. Stores message(s) with embeddings
4. Enqueues in deriver for observation extraction

## Deriver processing

After ~1 minute (DERIVER_STALE_SESSION_TIMEOUT_MINUTES), the deriver will:
- Read the messages
- Call the LLM (qwen3-nothink:latest)
- Extract structured observations
- Store them with vector embeddings

Then use `honcho-query` to retrieve what was learned.

## When to use

- User shares their preferences or requirements
- Technical decisions are made
- Important context is mentioned
- After a helpful debugging session
- When user explains their project structure
