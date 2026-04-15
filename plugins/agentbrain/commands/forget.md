---
name: forget
description: Delete a memory from AgentBrain. Use when user says "forget", "don't remember", "remove from memory", etc.
---

# Forget

Delete a memory from your AgentBrain.

## Usage

```
/forget "TypeScript"
/forget "database preference"
```

## What Happens

1. Finds matching memories (fuzzy name matching)
2. Shows what will be deleted
3. Deletes from both file system and vector database
4. Updates memory index

## Examples

```
/forget "TypeScript preference"
/forget "MongoDB"
/forget "testing approach"
```

## When to Use

Use `/forget` when the user wants to remove a memory:
- "Forget that..."
- "Don't remember..."
- "Remove that from memory"
- "I didn't mean that"
- "That's not right anymore"
