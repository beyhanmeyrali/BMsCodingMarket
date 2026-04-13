---
name: honcho-to-wiki
description: Use when exporting honcho-local memory data to LLM Wiki markdown format. Triggers: export to wiki, convert honcho to markdown, generate wiki pages, create Obsidian vault from memory, export agent memory.
allowed-tools: Read, Write, Bash(cd:*), Edit, Glob
---

# Honcho to Wiki Conversion

## Overview

Convert honcho-local memory storage (JSON) to LLM Wiki format (markdown files). This enables:
- Human-readable browsing of agent memory in Obsidian
- Git-tracked knowledge evolution
- Graph visualization of connections
- Integration with LLM Wiki ecosystem

## When to Use

Use when:
- User asks to "export honcho to wiki" or "convert memory to markdown"
- User wants to browse agent memory in Obsidian
- User asks for "wiki format" or "markdown export"
- Creating documentation from accumulated conversations

**Don't use when:**
- User just wants to query honcho memory (use `memory.chat()` instead)
- Working with raw JSON is preferred
- Real-time memory access is needed

## Data Mapping

| Honcho (JSON) | Wiki (Markdown) | Notes |
|---------------|-----------------|-------|
| `_storage["peers"]` | `wiki/peers/*.md` | One file per peer |
| `_storage["sessions"]` | `wiki/sessions/*.md` | One file per session |
| `_storage["messages"]` | Embedded in session pages | Full conversation log |
| `_storage["representations"]` | Embedded in peer pages | User profile/interests |
| Workspace ID | Wiki subdirectory | Isolates different projects |

## Wiki File Structure

```
wiki/
├── index.md              # Catalog (generated with links)
├── log.md                 # Export log (timestamped entries)
├── peers/                 # Entity pages
│   ├── {peer_id}.md      # One per user/agent
│   └── _index.md         # Peer catalog
└── sessions/              # Conversation pages
    ├── {session_id}.md  # One per conversation
    └── _index.md         # Session catalog
```

## Conversion Process

### Step 1: Read Honcho Storage

```python
import json
from pathlib import Path

# Read honcho storage
storage_path = "honco_workspace.json"  # or specified path
with open(storage_path, 'r') as f:
    storage = json.load(f)

peers = storage.get("peers", {})
sessions = storage.get("sessions", {})
messages = storage.get("messages", {})
representations = storage.get("representations", {})
```

### Step 2: Create Peer Pages

For each peer, create `wiki/peers/{peer_id}.md`:

```markdown
---
peer_id: {peer_id}
name: {name}
peer_type: {peer_type|user|agent}
created_at: {created_at}
workspace: {workspace_id}
---

# {name}

{description if available}

## Profile

{Auto-generated from representations}

### Interests

{list from representations.interests}

### Communication Style

{representations.communication_style}

### Frequent Topics

{list from representations.frequent_topics}

## Sessions

{List of sessions this peer participated in}
```

### Step 3: Create Session Pages

For each session, create `wiki/sessions/{session_id}.md`:

```markdown
---
session_id: {session_id}
created_at: {created_at}
workspace: {workspace_id}
participants:
  - {peer_name}
  - {agent_name}
---

# {Title (auto-generated or from metadata)}

## Summary

{LLM-generated summary of the conversation}

## Participants

- [[{peer_id}]] ({role})
- [[{agent_id}]] ({role})

## Transcript

{Full conversation log in chronological order}

### Timestamp
**{peer_name}:** {message}

## Topics

{Extracted topics and keywords}
```

### Step 4: Generate Index

Create `wiki/index.md` with catalog of all pages:

```markdown
# Honcho Wiki Index

## Peers

{List of all peer pages with one-line summaries}

## Sessions

{List of all session pages with one-line summaries}

## Statistics

- Total peers: {count}
- Total sessions: {count}
- Total messages: {count}
- Export date: {timestamp}
```

### Step 5: Update Log

Append to `wiki/log.md`:

```markdown
## [{timestamp}] export | honcho-to-wiki

**Workspace:** {workspace_id}
**Peers exported:** {count}
**Sessions exported:** {count}
**Messages exported:** {count}
**Output directory:** {wiki/}
```

## File Format Guidelines

### Frontmatter (YAML)

Every page MUST have YAML frontmatter:

```markdown
---
key: value
---
```

Required frontmatter fields:
- **Peer pages**: `peer_id`, `name`, `peer_type`, `workspace`
- **Session pages**: `session_id`, `created_at`, `workspace`, `participants`

### Obsidian Links

Use `[[Page Name]]` format for internal links:
- `[[user_123]]` - Link to peer page
- `[[conv-1]]` - Link to session page

### Markdown Best Practices

- Use ATX headings (`#`, `##`, `###`)
- Escape special characters in titles
- Use code blocks for technical content
- Keep lines under 100 characters
- Use lists for enumerations

## Implementation Notes

The conversion script (`scripts/to_wiki.py`) handles:
1. Reading honcho JSON storage
2. Creating wiki directory structure
3. Generating markdown files with proper frontmatter
4. Creating Obsidian-compatible links
5. Generating index.md catalog
6. Appending to log.md

### Error Handling

- Missing storage file: Clear error message with setup instructions
- Empty workspace: Still generates wiki structure with placeholder
- Malformed data: Skip invalid entries, log warnings
- File write errors: Clear error with permission fix suggestions

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Not creating directory structure | Files can't be written | Always mkdir -p peers/ sessions/ |
| Forgetting YAML frontmatter | Wiki won't parse correctly | Every page needs frontmatter |
| Using markdown links instead of Obsidian format | Links won't work in graph view | Use [[Page Name]] format |
| Not escaping special characters | Markdown may break | Escape or remove special chars |
| One giant index file | Defeats purpose of wiki | Separate pages, index just catalogs |

## Testing

After export, verify:

1. **File count**: Correct number of peers and sessions
2. **Frontmatter valid**: YAML parses correctly
3. **Links work**: Click links in Obsidian graph view
4. **Content complete**: Messages and representations present
5. **Index accurate**: All pages listed

## Integration with Obsidian

1. **Set vault path**: In Obsidian, open the `wiki/` folder
2. **Enable graph view**: See connections between entities
3. **Install plugins** (optional):
   - Dataview - Query wiki metadata
   - Graph Analysis - Visualize connections
   - Calendar - Timeline from log.md

## Red Flags - STOP and Reconsider

- Not creating separate peer/session pages
- Hardcoding paths instead of using workspace_id
- Forgetting to escape special characters in titles
- Not including frontmatter in wiki pages
- Overwriting existing wiki without backup
