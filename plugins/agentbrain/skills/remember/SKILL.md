---
name: remember
description: Explicitly store a fact, preference, or decision to memory for future retrieval.
---

# Remember

Store important information to your AgentBrain memory for automatic retrieval in future sessions.

## Natural Language Triggers (Recommended)

You don't need to use the `/remember` command! Just use natural language:

```
"Add to AgentBrain: we use PostgreSQL for all new projects"
"Remember that API routes should use kebab-case"
"Note that I prefer functional components"
"Don't forget we use TypeScript strict mode"
```

These phrases trigger immediate storage via the UserPromptSubmit hook.

## Manual Usage

```
/remember "We use PostgreSQL for all new projects"
/remember "API routes should use kebab-case"
/remember "User prefers functional components over class components"
/remember "Run tests before committing code"
```

## What Gets Stored

When you use `/remember`, the information is:

1. **Classified by type** - Automatically categorized as:
   - `user` - Personal preferences and habits
   - `project` - Project-specific decisions and conventions
   - `feedback` - Workflow guidance and corrections
   - `reference` - Links and external resources

2. **Scoped appropriately** - Set to the right access level:
   - `user:{username}` - Only you can see
   - `project:{reponame}` - Anyone working in this repo
   - `team:{teamname}` - Your team members (if configured)

3. **Embedded for search** - Converted to vector for semantic retrieval

4. **Indexed** - Added to MEMORY.md for reference

## Examples

### Storing Preferences
```
You: /remember "I always use TypeScript strict mode"

Stored: user_preferences.md
- Type: user
- Scope: user:bob
- Available: Immediately in future sessions
```

### Storing Project Decisions
```
You: /remember "We chose PostgreSQL over MongoDB for ACID compliance"

Stored: project_database_choice.md
- Type: project
- Scope: project:myapp
- Available: To anyone working on this project
```

### Storing Conventions
```
You: /remember "API endpoints use kebab-case, not snake_case"

Stored: api_naming_conventions.md
- Type: project
- Scope: project:myapi
- Available: Immediately in future sessions
```

## When to Use

Use `/remember` when:
- You make an important technical decision
- You establish a new convention
- You want to save a preference for later
- You discover a useful pattern or workaround

The memory will be automatically retrieved in future sessions when relevant.
