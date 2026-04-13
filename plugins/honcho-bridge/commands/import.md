---
name: honcho-import
description: Import markdown wiki files into Honcho memory. Parses Obsidian/Karpathy LLM Wiki format and creates Honcho peers, sessions, and messages.
---

# Wiki to Honcho Import

Import markdown wiki files (Obsidian/Karpathy LLM Wiki format) into Honcho memory.

## Usage

```bash
# Import wiki data into Honcho
python -m honcho_bridge.scripts.wiki_to_honcho \
  --base-url "http://localhost:8000" \
  --wiki-dir "wiki/" \
  --workspace "imported-wiki"
```

## Supported Format

Your wiki should follow this structure:

```
wiki/
├── peers/
│   ├── user_123.md       # Peer pages with YAML frontmatter
│   └── agent.md
└── sessions/
    ├── session-1.md      # Session transcripts
    └── session-2.md
```

## Peer Page Format

```markdown
---
peer_id: user_123
name: Alice
peer_type: user
created_at: 2024-01-01T00:00:00
---

# Alice

## Profile
- **Communication Style**: Direct
- **Interests**: Python, AI
```

## Session Page Format

```markdown
---
session_id: session-1
created_at: 2024-01-01T00:00:00
participants: [user_123, agent]
---

# Conversation

## Transcript
**Alice** (user): How do I use async?
**Agent** (assistant): Use async def...
```

## What Gets Imported

| Wiki Element | Honco Equivalent |
|--------------|------------------|
| `peers/*.md` | Peer records |
| `sessions/*.md` | Session records + messages |
| YAML frontmatter | Metadata |
| Transcript sections | Messages with peer attribution |

## Benefits

- **Bootstrap memory** from existing documentation
- **Human-editable** knowledge base
- **Round-trip** support (export → edit → import)
- **Obsidian integration** for visual editing

## Next Steps

After import, use Honco's API to query the imported knowledge:

```python
from honcho import Honcho

honcho = Honcho(workspace_id="imported-wiki")
user = honcho.peer("user_123")

# Chat about the imported knowledge
response = user.chat("What does this user know about?")
```
