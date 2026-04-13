---
name: wiki-to-honcho
description: Use when importing LLM Wiki markdown files into honcho-local memory. Enables agents to learn from wiki pages, ingest knowledge documentation, and convert Obsidian vaults to honcho memory format. Triggers: import wiki, wiki to honcho, ingest markdown, convert wiki to memory, learn from documentation.
allowed-tools: Read, Glob, Bash(grep:*), Write, Edit
---

# Wiki to Honcho Import

## Overview

Import LLM Wiki markdown files into honcho-local memory format. This enables:
- Learning from existing wiki documentation
- Converting Obsidian vaults to agent memory
- Building agent knowledge from structured markdown
- Ingesting external knowledge bases

## When to Use

Use when:
- User asks to "import wiki to honcho" or "convert markdown to memory"
- User has existing LLM Wiki or Obsidian vault
- User wants agent to learn from documentation
- Migrating from wiki-based to memory-based system

**Don't use when:**
- User just wants to export honcho (use `/honcho-to-wiki` instead)
- Working with raw JSON is preferred
- Wiki content is stale/unreliable

## Data Mapping (Reverse)

| Wiki (Markdown) | Honcho (JSON) | Notes |
|-----------------|---------------|-------|
| `peers/*.md` | `_storage["peers"]` | Parse frontmatter + content |
| `sessions/*.md` | `_storage["sessions"]` + `_storage["messages"]` | Extract transcript |
| YAML frontmatter | Peer metadata | Load into peer objects |
| Links `[[page]]` | Session associations | Parse wiki links |
| `index.md` | Overview/summary | Optional, used for context |

## Import Process

### Step 1: Scan Wiki Directory

```python
from pathlib import Path
import re
import yaml

wiki_path = Path("wiki")
peer_files = list(wiki_path.glob("peers/*.md"))
session_files = list(wiki_path.glob("sessions/*.md"))
```

### Step 2: Parse Peer Pages

```python
def parse_peer_page(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split frontmatter and content
    match = re.match(r'^---\\n(.*?)\\n---\\n(.*)', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
    else:
        return None
    
    peer_id = frontmatter.get('peer_id', file_path.stem)
    name = frontmatter.get('name', peer_id)
    peer_type = frontmatter.get('peer_type', 'user')
    
    return {
        'id': peer_id,
        'name': name,
        'peer_type': peer_type,
        'metadata': frontmatter
    }
```

### Step 3: Parse Session Pages

```python
def parse_session_page(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse frontmatter
    match = re.match(r'^---\\n(.*?)\\n---\\n(.*)', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
    else:
        return None
    
    session_id = frontmatter.get('session_id', file_path.stem)
    
    # Extract transcript from body
    messages = extract_transcript(body, frontmatter)
    
    return {
        'id': session_id,
        'metadata': frontmatter,
        'messages': messages
    }
```

### Step 4: Extract Messages from Transcript

```python
def extract_transcript(body, frontmatter):
    messages = []
    
    # Find transcript section
    in_transcript = False
    current_speaker = None
    
    for line in body.split('\\n'):
        if line.strip() == '## Transcript':
            in_transcript = True
            continue
        
        if not in_transcript:
            continue
        
        # Parse timestamped messages
        # Format: "### timestamp" followed by "**name** (role): content"
        if line.startswith('### '):
            current_speaker = None
        elif line.startswith('**') and '** ('):
            parts = line.split('** (', 1)
            if len(parts) > 1:
                name = parts[0].replace('**', '').strip()
                role_end = parts[1].find('):')
                if role_end > 0:
                    role = parts[1][:role_end]
                    current_speaker = (name, role)
        elif current_speaker and line.strip():
            name, role = current_speaker
            messages.append({
                'role': role,
                'content': line.strip(),
                'metadata': {'peer_id': name}
            })
    
    return messages
```

### Step 5: Build Honcho Storage

```python
def build_honcho_storage(peers, sessions):
    storage = {
        'peers': {},
        'sessions': {},
        'messages': {},
        'representations': {}
    }
    
    workspace = 'imported-wiki'
    
    # Add peers
    for peer in peers:
        peer_key = f"{workspace}:{peer['id']}"
        storage['peers'][peer_key] = peer
    
    # Add sessions and messages
    for session in sessions:
        session_key = f"{workspace}:{session['id']}"
        storage['sessions'][session_key] = session.get('metadata', {})
        storage['messages'][session_key] = session.get('messages', [])
    
    return storage
```

### Step 6: Write Honcho JSON

```python
import json

output_path = 'honco_imported-wiki.json'
with open(output_path, 'w') as f:
    json.dump(storage, f, indent=2)
```

## Handling Wiki Links

Obsidian uses `[[Page Name]]` format. When importing:

```python
def resolve_wiki_links(content, peer_map):
    # Find all [[links]]
    links = re.findall(r'\\[\\[([^\\]]+)\\]\\]', content)
    
    for link in links:
        # Check if link references a peer
        if link in peer_map:
            # Replace with peer_id reference
            content = content.replace(f'[[{link}]]', f'peer_id: {peer_map[link]}')
    
    return content
```

## Best Practices

### YAML Frontmatter

Wiki pages MUST have valid YAML frontmatter:

```yaml
---
peer_id: user_123
name: Alice
peer_type: user
created_at: 2026-04-13T...
---
```

Required fields for peer pages:
- `peer_id` - Unique identifier
- `name` - Display name
- `peer_type` - `user` or `agent`

Required fields for session pages:
- `session_id` - Unique identifier
- `participants` - List of peer_ids
- `created_at` - ISO timestamp

### Transcript Format

Expected format in session pages:

```markdown
## Transcript

### 2026-04-13 10:30

**user_123** (user): I need help with PO approval

**bot** (assistant): I can help with that.
```

Alternative format (simpler):

```markdown
## Transcript

**user_123:** I need help with PO approval

**bot:** I can help with that.
```

## Common Pitfalls

| Issue | Fix |
|-------|-----|
| Missing YAML frontmatter | Add frontmatter to all wiki pages |
| Invalid YAML syntax | Use yaml.safe_load() for robustness |
| Inconsistent transcript format | Support multiple formats |
| Broken wiki links | Validate peer_ids before linking |
| Character encoding issues | Specify utf-8 when reading |

## Testing Import

After import, verify:

1. **Peer count**: Correct number of peers imported
2. **Session count**: All sessions converted
3. **Message content**: Transcript preserved correctly
4. **Metadata**: Frontmatter data loaded
5. **Links**: Wiki links resolved or noted

## Implementation

Use the `wiki_to_honcho.py` script:

```bash
python scripts/wiki_to_honcho.py --wiki wiki/ --output honco_imported.json
```

Options:
- `--wiki`: Path to wiki directory
- `--output`: Output honcho JSON file
- `--workspace`: Workspace ID (default: imported-wiki)
- `--peers-only`: Only import peer pages, skip sessions
