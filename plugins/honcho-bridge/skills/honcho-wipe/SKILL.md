---
name: honcho-wipe
description: Clear all data from a Honcho workspace (peers, sessions, messages, observations). Destructive action — requires explicit confirmation. Use when starting fresh or cleaning up test data.
---

# Honcho Workspace Wipe

⚠️ **DESTRUCTIVE ACTION** — Deletes all data from a workspace.

## Usage

```bash
python plugins/honcho-bridge/scripts/honcho_wipe.py \
  --base-url http://localhost:8000 \
  --workspace <workspace-id> \
  --confirm
```

## Examples

```bash
# Preview what would be deleted (safe)
python plugins/honcho-bridge/scripts/honcho_wipe.py \
  --workspace test-workspace

# Actually delete (requires --confirm)
python plugins/honcho-bridge/scripts/honcho_wipe.py \
  --workspace test-workspace \
  --confirm
```

## What gets deleted

- All peers in the workspace
- All sessions
- All messages
- All observations (derived memory)

⚠️ **This cannot be undone** unless you have a wiki export.

## Safety workflow

Before wiping, consider exporting first:

```bash
# 1. Export to wiki
python plugins/honcho-bridge/scripts/to_wiki.py \
  --workspace my-workspace --output wiki-backup/

# 2. Verify the export
ls wiki-backup/

# 3. Then wipe
python plugins/honcho-bridge/scripts/honcho_wipe.py \
  --workspace my-workspace --confirm

# 4. Re-import if needed
python plugins/honcho-bridge/scripts/wiki_to_honcho.py \
  --workspace my-workspace --wiki wiki-backup/
```

## When to use

- Starting a fresh project in an existing workspace
- Cleaning up test data
- Before importing a clean wiki export
- Resetting after corruption issues

⚠️ **Never use --confirm on production workspaces without a backup!**
