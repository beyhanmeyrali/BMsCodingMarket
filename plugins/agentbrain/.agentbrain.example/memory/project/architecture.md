---
name: Project Architecture
description: Key architectural decisions for this project
type: project
scope: project:REPO_NAME
source: repo
# Trust Metadata - ADR (Architecture Decision Record)
source_type: adr
approval_status: approved
confidence: 0.9
owner: architecture-team
last_validated: 1713558000
# Domain Tags
domain_tags:
  - FastAPI
  - React
  - PostgreSQL
  - Qdrant
  - Docker
  - ECS
  - architecture
---

# Project Architecture

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: TypeScript, React
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Vector DB**: Qdrant (for AI features)

## Project Structure

```
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── scripts/       # Utility scripts
└── .agentbrain/   # Team memories
```

## Key Decisions

- **API Design**: RESTful with OpenAPI spec
- **Authentication**: JWT tokens with refresh flow
- **Logging**: Structured JSON logs to CloudWatch
- **Deployment**: Docker containers on ECS
