---
name: honcho-export
description: Export Honcho memory data to markdown wiki format (Karpathy LLM Wiki pattern). Creates Obsidian-compatible markdown files from Honcho peers, sessions, and messages.
---

# Honcho to Wiki Export

Export Honcho memory data to markdown format compatible with Obsidian and Karpathy's LLM Wiki pattern.

## Usage

```bash
# Export all data from a Honcho workspace
python -m honcho_bridge.scripts.to_wiki \
  --base-url "http://localhost:8000" \
  --workspace "my-workspace" \
  --output "wiki/"
```

## What Gets Exported

```
wiki/
├── index.md              # Catalog of all pages
├── log.md                # Export log
├── peers/                # Peer profile pages
│   ├── user_123.md
│   └── agent.md
└── sessions/             # Session transcripts
    ├── session-1.md
    └── session-2.md
```

## Page Format

### Peer Pages
```markdown
---
peer_id: user_123
name: Alice
peer_type: user
created_at: 2024-01-01T00:00:00
---

# Alice

## Profile
- **Communication Style**: Direct, technical
- **Interests**: Python, AI, Local LLMs

## Sessions
- [[session-1]] - First conversation
```

### Session Pages
```markdown
---
session_id: session-1
created_at: 2024-01-01T00:00:00
participants: [user_123, agent]
---

# Conversation - session-1

## Summary
Discussion about Python async patterns.

## Transcript
**user**: How do I use async/await?
**agent**: Use async def to define coroutines...
```

## Viewing in Obsidian

1. Open `wiki/` folder in Obsidian
2. Enable graph view to see connections
3. Use backlinks to navigate between peers and sessions

## Next Steps

Use `/honcho-import` to import wiki changes back to Honcho.
