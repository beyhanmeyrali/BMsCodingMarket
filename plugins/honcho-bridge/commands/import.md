---
name: honcho-import
description: Import markdown wiki files back into Honcho memory (peers, sessions, transcripts).
---

# Honcho Wiki Import

```bash
python plugins/honcho-bridge/scripts/wiki_to_honcho.py \
  --base-url http://localhost:8000 \
  --workspace <your-workspace> \
  --wiki wiki/
```

## What gets imported

| Wiki file | Honcho equivalent |
|-----------|-------------------|
| `peers/*.md` frontmatter | Peer identity + metadata |
| `sessions/*.md` `## Transcript` section | Messages attributed to each peer |

## Session page format

The import parser expects this transcript format (same as what export produces):

```markdown
## Transcript

### 2026-04-13 11:02

**Alice**:

Hey, what is the capital of France?

### 2026-04-13 11:02

**Bob**:

Paris.
```

> Importing the same session twice appends messages rather than replacing them — Honcho uses get-or-create semantics on session IDs.
