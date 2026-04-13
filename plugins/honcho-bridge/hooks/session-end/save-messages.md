---
name: honcho-session-end
description: Save session messages to Honcho memory when session ends. Ensures conversations are stored for future observation extraction.
---

# SessionEnd: Save Messages

Stores the current session's messages to Honcho for memory extraction.

## Configuration

```bash
HONCHO_WORKSPACE=my-project
HONCHO_PEER_ID=user
HONCHO_BASE_URL=http://localhost:8000
```

## What It Does

1. Captures all messages from the current session
2. Stores them in Honcho with embeddings
3. Deriver will extract observations within ~1 minute

## Storage Details

- User messages → stored with your peer ID
- Assistant messages → stored with "assistant" peer ID
- All messages embedded for semantic search
- Deriver processes after `DERIVER_STALE_SESSION_TIMEOUT_MINUTES`

## Python Script

The hook runs: `plugins/honcho-bridge/hooks/save_messages.py`
