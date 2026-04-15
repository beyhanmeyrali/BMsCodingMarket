---
name: forget
description: Remove a stored memory from AgentBrain. Deletes from both the vector database and file storage.
---

# Forget

Remove a memory from AgentBrain. The memory is deleted from both the vector database and file storage.

## Usage

```
/forget <memory-name>
```

Or by file:
```
/forget user_preferences.md
/forget project_database_choice.md
```

## What Happens

1. **Delete from Qdrant** - Memory is removed from vector search
2. **Delete file** - Markdown file is removed from memory directory
3. **Regenerate index** - MEMORY.md is updated to reflect the change

## Examples

```
You: /forget user_preferences

AgentBrain: Forgot memory: user_preferences.md
- Deleted from vector database
- Deleted file: C:/Users/bob/.claude/memory/user_preferences.md
- Memory index regenerated
```

## Finding Memory Names

If you're not sure of the exact name:

```
You: /recall "preferences"

AgentBrain: # Relevant Memories

## 1. user_preferences.md (relevance: 92%)
...

You: /forget user_preferences.md
```

## Confirmation

The forget operation is immediate. Be sure before using:

- Use `/recall` first to see what will be deleted
- Check the memory content to confirm it's the right one
- Use `/forget` with the exact filename

## Recovery

Once forgotten, memories cannot be recovered unless you have a backup.
