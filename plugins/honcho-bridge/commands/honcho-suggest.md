---
name: honcho-suggest
description: Get proactive suggestions from your memory based on current context and file.
---

# Honcho Memory Suggestions

Get proactive memory suggestions based on your current context, file, or branch.

## Usage

```
/honcho-suggest --context "src/auth/login.ts"
/honcho-suggest --branch "feature/auth"
/honcho-suggest --query "implementing oauth"
```

## Options

| Option | Description |
|--------|-------------|
| `--context`, `-c` | Current file or context |
| `--branch`, `-b` | Current git branch |
| `--query`, `-q` | Query for context-aware suggestions |
| `--conflicts` | Show conflicting observations |

## Examples

### Suggestions for current file
```
/honcho-suggest --context "src/auth/login.ts"
```

### Branch-specific suggestions
```
/honcho-suggest --branch "feature/database"
```

### Context-aware query
```
/honcho-suggest --query "I'm implementing authentication" --context "src/auth/*"
```

### Check for conflicts
```
/honcho-suggest --conflicts --query "using MongoDB"
```

## How It Works

The suggester combines:
1. Semantic search for relevant observations
2. Context filters (branch, files, tech stack)
3. Pattern detection for potential conflicts

## Output

Suggestions include:
- Relevant past decisions
- Your preferences for similar situations
- Potential conflicts with previous choices
- Related code patterns or solutions
