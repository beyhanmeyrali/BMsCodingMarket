---
name: remember
description: Store information to AgentBrain memory for future retrieval. Use when user says "remember", "don't forget", "keep in mind", etc.
---

# Remember

Store a fact, preference, or decision to your AgentBrain memory.

## Usage

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
/remember "We use PostgreSQL for all new projects"
/remember "API routes should use kebab-case"
/remember "User prefers functional components over class components"
/remember "Run tests before committing code"
```

## When to Use

Use `/remember` when the user indicates information should be stored:
- "Remember that..."
- "Don't forget..."
- "Keep in mind..."
- "Note that..."
- "For future reference..."
