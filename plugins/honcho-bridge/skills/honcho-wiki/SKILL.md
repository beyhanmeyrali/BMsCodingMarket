---
name: honcho-wiki
description: Use when exporting Honcho agent memory to human-readable wiki format (Obsidian/Karpathy LLM Wiki pattern) or importing wiki documentation into Honcho. Enables bidirectional knowledge sync between AI agent memory and markdown documentation. Triggers: export honcho memory, import wiki to honcho, create knowledge base from agent conversations, make agent memory human-readable, obsidian integration for agent memory, llm wiki pattern for agents, bootstrap agent from documentation.
---

# Honcho Wiki Bridge

**Bidirectional sync between Honcho agent memory and markdown wiki (Karpathy LLM Wiki pattern).**

## Overview

The Honcho Wiki Bridge connects AI agent memory with human-readable documentation:

```
Honcho Memory (Postgres) ←→ Markdown Wiki (Obsidian)
```

| Direction | Command | Purpose |
|-----------|---------|---------|
| Honcho → Wiki | `to_wiki.py` | Export agent memory to markdown |
| Wiki → Honcho | `wiki_to_honcho.py` | Import documentation to agent memory |

## Why Use This?

**Problem:** AI agent memory is locked in databases - humans can't read, edit, or verify it.

**Solution:** Export to markdown for:
- **Human oversight** - Verify what agents "know" about users
- **Knowledge management** - Build documentation from conversations
- **Editing** - Fix errors in agent memory using Obsidian
- **Bootstrapping** - Import existing docs into agent memory

## When to Use

**Export (Honcho → Wiki):**
- Agent has learned important user preferences
- Want to review what agent knows
- Building knowledge base from conversations
- Need to edit/correct agent memory

**Import (Wiki → Honcho):**
- Have existing documentation to teach agent
- Manually edited wiki and want to update agent
- Bootstrapping new agent with domain knowledge

## Export Format

```
wiki/
├── index.md              # Catalog
├── log.md                # Export log
├── peers/
│   ├── user_123.md       # User profiles
│   └── agent.md          # Agent profiles
└── sessions/
    ├── session-1.md      # Conversation transcripts
    └── session-2.md
```

### Peer Page Example

```markdown
---
peer_id: user_123
name: Beyhan MEYRALI
peer_type: user
created_at: 2024-01-01T00:00:00
workspace: my-agent
---

# Beyhan MEYRALI

**Type:** User
**Created:** 2024-01-01
**Sessions:** 5

## Profile

### Communication Style
Direct, technical, prefers concise answers

### Interests
- Local LLMs (Ollama)
- Python development
- AI agent architecture
- Knowledge management systems

### Frequent Topics
- Ollama setup
- Honcho memory integration
- Wiki export patterns

## Sessions
- [[session-1]] - Initial setup discussion
- [[session-2]] - Wiki export design
```

### Session Page Example

```markdown
---
session_id: session-1
title: Conversation - Initial Setup
created_at: 2024-01-01T00:00:00
workspace: my-agent
participants: [user_123, agent]
---

# Conversation - Initial Setup

## Summary

Discussion about setting up Honcho with Ollama for local AI agent memory.

## Participants

- **Beyhan MEYRALI** (user) - [[user_123]]
- **Assistant** (agent) - [[agent]]

## Transcript

### 2024-01-01 10:00
**Beyhan MEYRALI** (user):
How do I set up Honcho with Ollama?

**Assistant** (agent):
First install Ollama, then configure Honcho to use the OpenAI-compatible endpoint at http://localhost:11434/v1

## Topics

- Ollama
- Setup
- Configuration
```

## Import Format

Wiki files must have YAML frontmatter:

```yaml
---
peer_id: user_123
name: Beyhan MEYRALI
peer_type: user
---
```

Required fields:
- `peer_id` or `session_id`
- `name` (for peers) or `title` (for sessions)

## Quick Reference

### Export to Wiki

```python
from honcho import Honcho
from honcho_bridge.scripts.to_wiki import export_to_wiki

honcho = Honcho(workspace_id="my-agent")
export_to_wiki(honcho, output_dir="wiki/")
```

### Import from Wiki

```python
from honcho import Honcho
from honcho_bridge.scripts.wiki_to_honcho import import_from_wiki

honcho = Honcho(workspace_id="imported")
import_from_wiki(wiki_dir="wiki/", honcho=honcho)
```

## Integration with Official Honcho

This bridge works with **official Honcho** (https://github.com/plastic-labs/honcho):

1. Install official Honcho with Ollama
2. Run `/honcho-install` command
3. Export memory with `/honcho-export`
4. Edit in Obsidian
5. Import back with `/honcho-import`

## The Karpathy Connection

Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):

> "Knowledge should compound over time, not be re-derived every query"

This bridge extends the pattern to AI agents:
- **Karpathy**: Personal knowledge base
- **This bridge**: Agent memory + human knowledge base

## License

MIT License - Beyhan MEYRALI
