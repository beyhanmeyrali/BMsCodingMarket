---
name: promote
description: Promote a memory to a wider scope for sharing with others
---

Promote a memory to a wider scope (team/project/org) so others can benefit from it.

## Usage

```
/promote <memory-name> --to <scope>
```

## Examples

- `/promote testing_patterns --to team:platform` - Share with your team
- `/promote api_decisions --to project:myapi` - Share with the project
- `/promote conventions --to org:acme` - Share company-wide

## Scopes

- `user:{username}` - Personal (default for new memories)
- `team:{teamname}` - Team members only
- `project:{reponame}` - Anyone in the repository
- `org:{orgname}` - Entire organization

## What Happens

1. Memory scope is updated in the file
2. Vector database is updated with new scope
3. Memory is now visible to others in the new scope
4. MEMORY.md index is regenerated
