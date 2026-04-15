---
name: recall
description: Search your stored memories by semantic meaning
---

Search your AgentBrain memories by semantic meaning to find relevant information from past sessions.

This command performs vector-based semantic search on your stored memories, finding results based on meaning rather than exact keyword matches.

## Usage

```
/recall "your search query"
```

## Examples

- `/recall "authentication decisions"` - Find how authentication was handled
- `/recall "testing patterns"` - Find testing conventions
- `/recall "database schema"` - Find database-related decisions
- `/recall "api error handling"` - Find error handling patterns

## How It Works

1. Your query is converted to a vector embedding using Ollama
2. Qdrant searches for semantically similar memories
3. Results are filtered to only show memories you have access to
4. Top results are returned with relevance scores
