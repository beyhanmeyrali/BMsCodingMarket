---
name: Team Conventions
description: Shared coding conventions and patterns for the team
type: team
scope: team:platform
source: repo
# Trust Metadata
source_type: manual
approval_status: approved
confidence: 0.8
owner: platform-team
last_validated: 1713558000
# Domain Tags
domain_tags:
  - Python
  - PEP8
  - testing
  - workflow
---

# Team Conventions

## Code Style

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for public APIs

## Workflow

- Create feature branches from `main`
- Use descriptive branch names: `feature/description`, `fix/bug-description`
- Require one approval before merging
- Update CHANGELOG on significant changes

## Testing

- Write tests for new features
- Maintain >80% code coverage
- Run tests locally before pushing
