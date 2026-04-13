---
name: honcho-store
description: Store information to Honcho memory for later retrieval. Use this to save preferences, decisions, or context that should be remembered.
---

# Store to Honcho Memory

Store a fact, preference, or decision to your Honcho memory.

## Usage

```
/honcho-store "I prefer TypeScript for frontend projects"
```

## What Happens

1. The message is stored with embeddings
2. Deriver processes it in ~1 minute
3. Extracted observations become available for future queries

## Examples

```
/honcho-store "I work in fintech building trading systems"
/honcho-store "I use Neovim as my editor"
/honcho-store "I test code before committing"
```

## Configuration

Set your workspace and peer ID:
```bash
export HONCHO_WORKSPACE=my-project
export HONCHO_PEER_ID=user
```
