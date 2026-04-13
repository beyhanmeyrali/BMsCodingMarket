---
name: honcho-export
description: Export Honcho memory to Obsidian-compatible markdown wiki files (peers, sessions, transcripts).
---

# Honcho Wiki Export

```bash
python plugins/honcho-bridge/scripts/to_wiki.py \
  --base-url http://localhost:8000 \
  --workspace <your-workspace> \
  --output wiki/
```

**Cloud (official plugin):** replace `--base-url` with your Honcho API endpoint, or omit it if `HONCHO_ENDPOINT` is set.

## Output structure

```
wiki/
├── index.md              # catalog with stats
├── peers/
│   └── <peer-id>.md      # one page per user/agent identity
└── sessions/
    └── <session-id>.md   # full transcript with participants
```

Open `wiki/` in [Obsidian](https://obsidian.md) for graph view — peers and sessions link to each other via `[[wikilinks]]`.

## Next step

Edit the markdown files, then use `/honcho-import` to push corrections back into Honcho.
