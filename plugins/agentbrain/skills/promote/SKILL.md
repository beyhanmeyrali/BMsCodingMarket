---
name: promote
description: Promote a memory from personal to team/project scope for sharing with others.
---

# Promote Memory

Promote a memory to a wider scope so it can be shared with your team or project members.

## Usage

```
/promote <memory-name> --to <scope>
```

## Scopes

| Scope | Who Can See | Use For |
|-------|-------------|---------|
| `user:{username}` | Only you | Personal preferences, workflow |
| `team:{teamname}` | Team members | Shared conventions, patterns |
| `project:{reponame}` | Anyone in repo | Project decisions, architecture |
| `org:{orgname}` | Everyone | Company-wide policies |

## Examples

### Promote to Team
```
You: /promote testing_patterns --to team:platform

Promoted: testing_patterns.md
- From: user:bob
- To: team:platform
- Now visible to: 15 team members
```

### Promote to Project
```
You: /promote api_auth_decision --to project:myapi

Promoted: api_auth_decision.md
- From: user:bob
- To: project:myapi
- Now visible to: Anyone working on this repository
```

## When to Promote

Promote memories when:
- **Pattern is widely useful** - Others would benefit from knowing
- **Decision affects everyone** - Architecture choices, conventions
- **Team should adopt** - Best practices, workflows

## Promotion Workflow

1. **Personal memory** - Created during session (user scope)
2. **Validated by use** - Retrieved frequently, proves useful
3. **Promoted** - Moved to team/project scope
4. **Shared** - Others can now access and benefit

## Approval (Future)

In future versions, team/project promotions may require approval via:
- Pull request review
- Codeowner approval
- Team consensus

Current implementation allows direct promotion for flexibility.
