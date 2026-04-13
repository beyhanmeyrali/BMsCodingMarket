---
name: honcho-session-start
description: Load user's memory from Honcho at session start. Shows observations about the user including preferences, stack, and past context.
---

# SessionStart: Load User Memory

Loads what Honcho has learned about the user and displays it at session start.

## Configuration

Set these environment variables:

```bash
HONCHO_WORKSPACE=my-project          # Your workspace ID
HONCHO_PEER_ID=user                  # Your peer ID (default: "user")
HONCHO_BASE_URL=http://localhost:8000  # Local Honcho API
```

## What It Does

1. Connects to local Honcho at session start
2. Queries for relevant observations about the user
3. Displays context: preferences, stack, past decisions

## Output Example

```
🧠 Honcho Memory Loaded for: user

About this user:
- Prefers Neovim for TypeScript development
- Works in fintech building trading systems
- Likes concise answers, gets straight to the point
- Uses PostgreSQL, avoids MongoDB
```

## Python Script

The hook runs: `plugins/honcho-bridge/hooks/load_memory.py`

```python
# Query: "What do you know about this user?"
# Displays observations that help contextualize the conversation
```
