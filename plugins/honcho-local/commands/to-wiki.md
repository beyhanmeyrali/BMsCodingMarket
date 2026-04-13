---
name: honcho-to-wiki
description: Export honcho-local memory data to LLM Wiki markdown format for browsing in Obsidian or other markdown viewers
---

# Honcho to Wiki Export

Export honcho-local memory data as markdown files compatible with [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## What Gets Exported

| Honcho Data | Becomes | File |
|-------------|---------|------|
| Peers (users/agents) | Entity pages | `wiki/peers/{peer_id}.md` |
| Sessions | Conversation logs | `wiki/sessions/{session_id}.md` |
| Representations | Profile summaries | Embedded in entity pages |
| Messages | Threaded content | Embedded in session pages |
| Metadata | YAML frontmatter | All pages |

## Usage

```
/honcho-to-wiki
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--workspace` | `local-workspace` | Honcho workspace to export |
| `--output` | `wiki/` | Output directory for wiki files |
| `--include-messages` | `true` | Include full message content |
| `--sessions-only` | `false` | Only export sessions, skip peer pages |
| `--update-index` | `true` | Regenerate index.md |

## Output Structure

```
wiki/
├── index.md          # Catalog of all wiki pages
├── log.md            # Export log with timestamp
├── peers/
│   ├── user_123.md   # User profile + conversation history
│   └── agents.md     # Agent profiles
└── sessions/
    ├── conv-1.md     # Conversation summaries
    └── conv-2.md
```

## Wiki File Format

### Entity Pages (peers/*.md)

```markdown
---
peer_id: user-123
name: Alice
peer_type: user
created_at: 2026-04-13T...
sessions: 3
last_active: 2026-04-13T...
---

# Alice

## Profile

[Auto-generated representation from honcho]

## Interests

- Topic 1
- Topic 2

## Communication Style

Direct, prefers brief answers

## Sessions

- [[conv-1]] - PO approval help
- [[conv-2]] - Follow-up questions
```

### Session Pages (sessions/*.md)

```markdown
---
session_id: conv-1
created_at: 2026-04-13T...
participants: [user_123, bot]
message_count: 5
---

# Conversation: PO Approval Help

## Summary

[Auto-generated summary]

## Transcript

**user_123:** I need PO approval help

**bot:** I can help with that...

## Topics Discussed

- PO approval process
- Urgent requests
- Vendor management
```

## Post-Export

1. **Open in Obsidian**: Set the `wiki/` folder as your Obsidian vault
2. **Enable Graph View**: See connections between entities and sessions
3. **Backlinks Work**: Links between pages are Obsidian-compatible
4. **Git Track**: Commit wiki changes to track knowledge evolution

## Related

- [LLM Wiki Pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- honcho-local documentation
- Obsidian documentation
