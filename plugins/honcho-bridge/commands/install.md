---
name: honcho-install
description: Set up local Honcho memory with Docker + Ollama. Full offline setup with wiki export/import capabilities.
---

# Local Honcho Setup for Claude Code

## Step 1 — Install Honcho dependencies

```bash
pip install honcho-ai pyyaml
```

## Step 2 — Start local Honcho server

Follow the full setup guide in **[`docs/HONCHO_SETUP_GUIDE.md`](../../../docs/HONCHO_SETUP_GUIDE.md)**:

1. Clone honcho server: `E:\workspace\honcho`
2. Apply source patches for local Ollama
3. Configure `.env` for localhost:8000
4. Run `docker compose up -d --build`

Your Honcho API will be available at `http://localhost:8000`.

## Step 3 — Verify connection

```bash
python -c "
import honcho as h
client = h.Honcho(base_url='http://localhost:8000', api_key='placeholder', workspace_id='test')
print('Connected!' if list(client.peers()) is not None else 'Failed')
"
```

## Step 4 — Use this plugin

- `/honcho-export` - Dump memory to Obsidian-compatible markdown
- `/honcho-import` - Restore edited markdown back to Honcho
- `honcho-wiki` skill - Full wiki round-trip workflow

## Quick test

```bash
# Create a test peer and session
python -c "
import honcho as h
client = h.Honcho(base_url='http://localhost:8000', api_key='placeholder', workspace_id='test-workspace')
peer = client.peer('alice', metadata={'name': 'Alice'})
session = client.session('test-session')
session.add_messages([peer.message('I prefer Python and vim.')])
print('Message stored. Wait ~1 min for deriver, then export.')
"

# Export after ~1 minute (for deriver to process)
python plugins/honcho-bridge/scripts/to_wiki.py --workspace test-workspace --output test-wiki/
```
