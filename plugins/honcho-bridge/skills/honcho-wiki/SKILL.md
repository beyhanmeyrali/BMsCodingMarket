---
name: honcho-wiki
description: Export Honcho memory to readable markdown and import it back. Use when you want to audit, edit, or back up what Honcho knows. Requires the official claude-honcho plugin (plastic-labs/claude-honcho) for memory collection — this skill only handles the wiki round-trip.
---

# Honcho Wiki Bridge

Export Honcho memory to Obsidian-compatible markdown, edit it as plain text, import changes back.

## Export

```bash
python plugins/honcho-bridge/scripts/to_wiki.py \
  --base-url http://localhost:8000 \
  --workspace <workspace-id> \
  --output wiki/
```

Produces `wiki/peers/*.md` and `wiki/sessions/*.md`. Open in Obsidian to see graph view with peer ↔ session links.

## Import

```bash
python plugins/honcho-bridge/scripts/wiki_to_honcho.py \
  --base-url http://localhost:8000 \
  --workspace <workspace-id> \
  --wiki wiki/
```

Reads YAML frontmatter for peer identity and `## Transcript` sections for messages.

## Peer page format

```markdown
---
peer_id: alice
name: Alice
peer_type: user
---

# Alice
```

## Session page format

```markdown
---
session_id: session-001
participants: [alice, bob]
---

## Transcript

### 2026-04-13 11:02

**Alice**:

What should we build next?

### 2026-04-13 11:03

**Bob**:

Let's add wiki export.
```

## When to use this

- Verify what Honcho actually extracted from your conversations
- Correct a wrong observation by editing the markdown and re-importing
- Bootstrap a new workspace from existing documentation
- Back up memory before wiping a workspace

## Prerequisites

- Official Honcho plugin installed: `plastic-labs/claude-honcho`
- `pip install honcho-ai pyyaml`
- Honcho server running (cloud via [app.honcho.dev](https://app.honcho.dev), or local — see `docs/HONCHO_SETUP_GUIDE.md`)
