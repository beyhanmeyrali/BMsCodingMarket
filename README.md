# honcho-bridge

> Wiki export/import for [Honcho](https://github.com/plastic-labs/honcho) memory. Companion to the official [claude-honcho](https://github.com/plastic-labs/claude-honcho) plugin.

## What this is

The official [plastic-labs/claude-honcho](https://github.com/plastic-labs/claude-honcho) plugin handles everything you need for persistent Claude Code memory — `SessionStart` context loading, message saving, `PreCompact` snapshots, MCP tools. **Use that first.**

This plugin adds one thing the official plugin doesn't have: **wiki export/import** — the ability to dump your Honcho memory to readable, editable markdown files (Obsidian-compatible) and import them back.

This is useful for:
- Reading and auditing what Honcho actually knows about you
- Manually correcting wrong memories
- Bootstrapping a fresh workspace from existing docs
- Sharing/backing up memory as plain text

## Setup

### 1. Install the official Honcho plugin

```
/plugin marketplace add plastic-labs/claude-honcho
/plugin install honcho@honcho
```

Get your API key at [app.honcho.dev](https://app.honcho.dev). Follow the [official setup instructions](https://github.com/plastic-labs/claude-honcho).

**Running locally (no API key)?** See [`docs/HONCHO_SETUP_GUIDE.md`](docs/HONCHO_SETUP_GUIDE.md) for the full local Ollama + Docker stack setup.

### 2. Install this plugin

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install honcho-bridge@bms-marketplace
```

### 3. Install Python dependencies

```bash
pip install honcho-ai pyyaml
```

## Commands

| Command | Description |
|---------|-------------|
| `/honcho-export` | Export Honcho workspace to markdown wiki |
| `/honcho-import` | Import markdown wiki back into Honcho |

## Wiki Export

```bash
python plugins/honcho-bridge/scripts/to_wiki.py \
  --base-url http://localhost:8000 \
  --workspace my-workspace \
  --output wiki/
```

Creates:
```
wiki/
├── index.md          # catalog
├── peers/            # one page per user/agent identity
└── sessions/         # full conversation transcripts
```

Open the `wiki/` folder in [Obsidian](https://obsidian.md) for graph view and backlink navigation.

## Wiki Import

```bash
python plugins/honcho-bridge/scripts/wiki_to_honcho.py \
  --base-url http://localhost:8000 \
  --workspace my-workspace \
  --wiki wiki/
```

Reads YAML frontmatter + `## Transcript` sections from session pages and re-creates peers, sessions, and messages in Honcho.

## Local Stack (Ollama, no API key)

The official plugin supports local endpoints:

```bash
export HONCHO_ENDPOINT="local"   # points to http://localhost:8000
```

For the full Docker + Ollama setup (including required source patches for local embedding models), see [`docs/HONCHO_SETUP_GUIDE.md`](docs/HONCHO_SETUP_GUIDE.md).

## Links

- [Honcho](https://github.com/plastic-labs/honcho) — the memory platform
- [claude-honcho](https://github.com/plastic-labs/claude-honcho) — official Claude Code plugin
- [app.honcho.dev](https://app.honcho.dev) — get your API key
- [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — inspiration for the wiki bridge
