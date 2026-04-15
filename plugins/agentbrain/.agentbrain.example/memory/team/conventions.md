---
name: Team Conventions
description: Shared coding conventions and patterns for the team
type: team
scope: team:platform
source: repo
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
