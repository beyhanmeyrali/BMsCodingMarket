---
name: honcho-status
description: Check Honcho system health including API connection, deriver status, observation counts, and workspace statistics. Use when verifying the memory system is working correctly.
---

# Honcho System Status

Check the health and statistics of your local Honcho memory system.

## Usage

```bash
python plugins/honcho-bridge/scripts/honcho_status.py \
  --base-url http://localhost:8000 \
  --workspace <workspace-id>
```

## Examples

```bash
# Check default workspace
python plugins/honcho-bridge/scripts/honcho_status.py \
  --workspace my-project

# Check with custom endpoint
python plugins/honcho-bridge/scripts/honcho_status.py \
  --base-url http://localhost:8000 \
  --workspace my-project
```

## What it shows

1. **Connection** - API health and latency
2. **Workspace** - Current workspace info
3. **Peers** - Total peer count
4. **Sessions** - Total session count
5. **Messages** - Total message count
6. **Observations** - Total observation count (deriver output)
7. **Deriver Status** - Whether background worker is processing

## Interpreting results

| Metric | What it means |
|--------|---------------|
| High messages, low observations | Deriver hasn't processed yet (wait ~1 min) or is failing |
| Zero observations | Deriver may not be running — check Docker logs |
| Connection failed | Honcho API is down — restart with `docker compose up -d` |
| High latency | Ollama may be overloaded — check `ollama ps` |

## When to use

- After starting Honcho — verify it's working
- After storing messages — confirm deriver processed them
- When queries return empty — check if observations exist
- Troubleshooting — get a full system health picture
