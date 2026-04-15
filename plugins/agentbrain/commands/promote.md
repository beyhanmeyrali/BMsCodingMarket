---
name: promote
description: Promote a memory to wider scope (team/project/org). Use when user says "share with team", "team convention", etc.
---

# Promote

Promote a memory to a wider scope for team sharing.

## Usage

```
/promote <memory_name> --to team:platform
/promote <memory_name> --to project:myapp
/promote <memory_name> --to org:company
```

## What Happens

1. Finds the memory by name (fuzzy matching)
2. Updates its scope to the target
3. Re-stores in vector database with new scope
4. Now visible to all members of that scope

## Scopes

- `team:{name}` - All team members can see
- `project:{name}` - Anyone working on this project
- `org:{name}` - Everyone in organization

## Examples

```
/promote api_conventions --to team:platform
/promote database_choice --to project:myapp
/promote testing_practices --to org:acme
```

## When to Use

Use `/promote` when the user indicates information should be shared:
- "This would be good for the team to know"
- "Share this with the team"
- "Make this a team convention"
- "Everyone should know this"
