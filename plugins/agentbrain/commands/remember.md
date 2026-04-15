---
name: remember
description: Store information to AgentBrain memory. ALSO TRIGGERED AUTOMATICALLY by phrases like "add to AgentBrain", "remember that", "don't forget", etc.
---

# Remember

Store a fact, preference, or decision to your AgentBrain memory.

## Automatic Triggers

NO NEED TO CALL `/remember` DIRECTLY! The UserPromptSubmit hook automatically captures:

- "Add to AgentBrain: ..."
- "Add that to AgentBrain"
- "Save to AgentBrain: ..."
- "Remember that ..."
- "Don't forget ..."
- "Keep in mind ..."
- "Note that ..."

## Manual Usage

```
/remember "I prefer TypeScript over JavaScript"
```

## What Happens

1. Information is classified by type (user/project/feedback/reference)
2. Appropriate scope is assigned (user/project/team)
3. Memory is stored as markdown file
4. Embedded and added to vector database
5. Automatically retrieved when relevant in future sessions

## Examples

```
User: "Add to AgentBrain: we use Redis for caching"
→ Automatic: Stored immediately

User: "Remember that I prefer TypeScript over JavaScript"
→ Automatic: Stored immediately

/remember "We use PostgreSQL for all new projects"
/remember "API routes should use kebab-case"
```
