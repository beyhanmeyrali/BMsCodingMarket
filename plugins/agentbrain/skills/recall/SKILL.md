---
name: recall
description: Search your stored memories by semantic meaning. Finds relevant memories based on what you mean, not just keywords.
---

# Recall Memory

Search your AgentBrain memories by meaning and context. Unlike keyword search, semantic search understands what you're looking for and finds related memories even if they don't contain the exact words.

## Usage

```
/recall "how do we handle authentication"
/recall "typescript configuration patterns"
/recall "testing conventions"
/recall "what did we decide about the database"
```

## What Happens

1. **Embed your query** - Your question is converted to a vector embedding
2. **Search with scope filtering** - Only memories you have access to are searched
3. **Return relevant memories** - Top results ranked by semantic similarity

## Scope Filtering

Results automatically respect your access level:
- **Personal** - Only your memories
- **Team** - Memories shared with your team (if configured)
- **Project** - Memories for the current repository
- **Organization** - Company-wide memories (if configured)

## Output Format

Results show:
- Memory file name
- Relevance score (percentage)
- Memory type (user/feedback/project/reference)
- Scope (who can see this memory)
- Full memory content

## Examples

```
You: /recall "authentication"

AgentBrain: # Relevant Memories (3 found)

## 1. api_auth_decisions.md (relevance: 87%)
**Type:** project | **Scope:** project:myapi

# API Authentication Decisions

We use JWT tokens for API authentication with the following flow:
...

## 2. user_preferences.md (relevance: 65%)
**Type:** user | **Scope:** user:bob

## Authentication Preferences

- Prefers token-based auth over sessions
- Always include refresh token handling
...
```

## Tips

- **Be specific** - "error handling in API routes" works better than "errors"
- **Use natural language** - Ask questions like you would to a colleague
- **Follow up** - Use the memory file name to `/recall` more from that file
