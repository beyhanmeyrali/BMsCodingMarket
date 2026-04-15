---
name: recall
description: Retrieve relevant memories from AgentBrain. Use when user asks "what did I say", "what do you know", "remind me", etc.
---

# Recall

Retrieve relevant memories from your AgentBrain using semantic search.

## Usage

```
/recall "testing approach"
/recall "database preferences"
/recall "deployment process"
```

## What Happens

1. Query is converted to embedding vector
2. Semantic search finds relevant memories
3. Results are ranked by relevance
4. Top memories are returned with context

## Examples

```
/recall "What did I say about testing?"
/recall "database"
/recall "authentication"
/recall "API conventions"
```

## When to Use

Use `/recall` when the user asks about past information:
- "What did I say about...?"
- "What do you know about...?"
- "Have I told you about...?"
- "Remind me about..."
- "How do we handle...?"
