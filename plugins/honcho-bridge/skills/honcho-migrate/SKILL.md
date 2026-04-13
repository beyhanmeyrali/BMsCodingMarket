---
name: honcho-migrate
description: Copy or move data between Honcho workspaces. Useful for reorganizing memory, archiving old sessions, or merging user data. Supports both copy (keep source) and move (delete source) modes.
---

# Honcho Workspace Migration

Copy or move data between workspaces.

## Usage

```bash
# Copy (keep source intact)
python plugins/honcho-bridge/scripts/honcho_migrate.py \
  --base-url http://localhost:8000 \
  --source <source-workspace> \
  --destination <dest-workspace> \
  --mode copy

# Move (delete from source)
python plugins/honcho-bridge/scripts/honcho_migrate.py \
  --base-url http://localhost:8000 \
  --source <source-workspace> \
  --destination <dest-workspace> \
  --mode move
```

## Examples

```bash
# Archive old sessions to a separate workspace
python plugins/honcho-bridge/scripts/honcho_migrate.py \
  --source my-project --destination my-project-archive \
  --mode move

# Copy a specific peer's data
python plugins/honcho-bridge/scripts/honcho_migrate.py \
  --source temp-workspace --destination main-workspace \
  --peer alice --mode copy

# Merge all data from a test workspace
python plugins/honcho-bridge/scripts/honcho_migrate.py \
  --source test --destination production \
  --mode move
```

## Modes

| Mode | Source | Destination |
|------|--------|-------------|
| `copy` | Kept intact | Data added |
| `move` | Deleted | Data added |

## What gets migrated

- Peers (with metadata)
- Sessions (with metadata)
- Messages (with embeddings)
- Observations (if available in SDK)

## Use cases

- **Archiving**: Move old sessions to `project-archive` workspace
- **Cleanup**: Consolidate scattered test workspaces
- **Reorganization**: Split a workspace by user or project
- **Backup**: Copy to a backup workspace before changes
- **Merge**: Combine data from multiple sources

## Safety tips

1. **Preview first**: Run with `--dry-run` to see what will happen
2. **Copy mode**: Use `copy` mode first to verify
3. **Export backup**: Use `/honcho-export` before `move` mode
4. **Test peer**: Try with `--peer` flag for single peer first
