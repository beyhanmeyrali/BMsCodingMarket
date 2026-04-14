---
name: honcho-search
description: Advanced semantic search with code context filters. Search your memory by file patterns, time ranges, or memory levels.
---

# Honcho Memory Search

Search your Honcho memory with advanced filters for file patterns, time ranges, and memory levels.

## Usage

```
/honcho-search "authentication decisions" --file-pattern "src/auth/*"
/honcho-search "what did we decide about the database"
/honcho-search "my preferences" --memory-type global
```

## Options

| Option | Description |
|--------|-------------|
| `--file-pattern`, `-f` | Filter by file pattern (glob) |
| `--after`, `-a` | Results after date (YYYY-MM-DD or 30d) |
| `--before` | Results before date |
| `--memory-type`, `-t` | Filter by level (global, project, file, context) |
| `--limit`, `-l` | Max results (default: 10) |
| `--verbose`, `-v` | Show detailed metadata |

## Examples

### Search by file pattern
```
/honcho-search "how to handle errors" --file-pattern "src/**/*.py"
```

### Search recent memories
```
/honcho-search "project decisions" --after 7d
```

### Search global preferences
```
/honcho-search "my coding preferences" --memory-type global
```

### Combined filters
```
/honcho-search "database schema" --file-pattern "**/*.sql" --after 2024-01-01 --limit 5
```

## Memory Levels

- **global**: User preferences across all projects
- **project**: Project-specific decisions and context
- **file**: Specific file-related knowledge
- **context**: Session-specific information
