---
name: remember
description: Explicitly store a fact, preference, or decision to memory
---

Store important information to your AgentBrain memory for automatic retrieval in future sessions.

## Usage

```
/remember "information to remember"
```

## Examples

- `/remember "We use PostgreSQL for user data"` - Store a technical decision
- `/remember "I prefer functional components"` - Store a personal preference
- `/remember "API routes use kebab-case"` - Store a convention
- `/remember "Test before committing"` - Store a workflow rule

## What Happens

1. The information is classified by type (user/project/feedback/reference)
2. An appropriate scope is assigned (user/project/team)
3. The memory is stored as a markdown file
4. It's embedded and added to the vector database
5. It's automatically retrieved when relevant in future sessions
