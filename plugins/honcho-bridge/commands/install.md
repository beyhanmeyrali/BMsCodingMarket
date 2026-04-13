---
name: honcho-install
description: Set up Honcho memory for Claude Code — installs the official claude-honcho plugin and optionally configures a local Ollama stack if you want to run without an API key.
---

# Honcho Setup for Claude Code

## Step 1 — Install the official Honcho plugin

The official plugin from Plastic Labs handles session memory, context loading, and MCP tools.

```
/plugin marketplace add plastic-labs/claude-honcho
/plugin install honcho@honcho
```

Get your API key at **[app.honcho.dev](https://app.honcho.dev)**, then set it:

**macOS / Linux:**
```bash
export HONCHO_API_KEY="hch-your-key-here"
```

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable("HONCHO_API_KEY", "hch-your-key-here", "User")
```

Restart Claude Code. You should see Honcho context loading at session start.

Full official docs: [github.com/plastic-labs/claude-honcho](https://github.com/plastic-labs/claude-honcho)

---

## Step 2 — Install this plugin (wiki export/import)

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install honcho-bridge@bms-marketplace
pip install honcho-ai pyyaml
```

Use `/honcho-export` and `/honcho-import` to dump/restore memory as readable markdown.

---

## Running locally without an API key?

Set the official plugin to use your local server:

```bash
export HONCHO_ENDPOINT="local"   # expects Honcho at http://localhost:8000
```

Then follow [`docs/HONCHO_SETUP_GUIDE.md`](../../../docs/HONCHO_SETUP_GUIDE.md) to stand up the full Docker + Ollama stack locally.
