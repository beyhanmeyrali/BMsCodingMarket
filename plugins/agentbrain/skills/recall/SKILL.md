---
name: recall
description: Search your stored memories by semantic meaning. Finds relevant memories based on what you mean, not just keywords. Supports retrieval modes and domain filtering.
---

# Recall Memory

Search your AgentBrain memories by meaning and context. Unlike keyword search, semantic search understands what you're looking for and finds related memories even if they don't contain the exact words.

## Usage

```
/recall "how do we handle authentication"
/recall "typescript configuration patterns"
/recall "testing conventions"
/recall "what did we decide about the database"
```

## Retrieval Modes

You can specify what type of memory to retrieve:

| Mode | Description | Filters By |
|------|-------------|------------|
| `similar_incidents` | Find related incidents | source: incident |
| `conventions` | Team conventions and preferences | source: manual/auto, types: feedback/project |
| `approved_standards` | Officially approved standards | status: approved, confidence ≥ 0.8 |
| `example_solutions` | Working solutions from PRs/incidents | source: pr/incident |
| `architecture_decisions` | ADRs and architecture decisions | source: adr, status: approved |

```
/recall "authentication issues" --mode similar_incidents
/recall "naming conventions" --mode conventions
/recall "api standards" --mode approved_standards
/recall "RAP handlers" --mode example_solutions --domain-tags RAP CDS
```

## Domain Tag Filtering

Filter by technical domains or project tags:

```
/recall "transport errors" --domain-tags SAP Transport
/recall "clean core" --domain-tags Clean_Core ABAP_Cloud
/recall "RAP patterns" --domain-tags RAP CDS
```

Common domain tags for SAP development:
- **RAP** - RESTful Application Programming
- **CDS** - Core Data Services
- **ABAP_Cloud** - ABAP Cloud development
- **Transport** - Transport requests
- **ATC** - ABAP Test Cockpit
- **Clean_Core** - Clean Core methodology
- **BTP** - SAP Business Technology Platform
- **S4HANA_Cloud** - S/4HANA Cloud

## What Happens

1. **Embed your query** - Your question is converted to a vector embedding
2. **Apply retrieval mode filters** - Source type, approval status, confidence
3. **Apply domain tag filters** - Only memories matching tags are returned
4. **Search with scope filtering** - Only memories you have access to are searched
5. **Return relevant memories** - Top results ranked by semantic similarity

## Scope Filtering

Results automatically respect your access level:
- **Personal** - Only your memories
- **Team** - Memories shared with your team (if configured)
- **Project** - Memories for the current repository
- **Organization** - Company-wide memories (if configured)

## Output Format

Results show:
- Memory file name
- Relevance score (percentage)
- Trust indicator (✓ = approved, ~ = draft/unapproved)
- Confidence score (percentage)
- Source type (manual, pr, adr, incident, auto_captured)
- Approval status (draft, approved, archived, superseded)
- Domain tags
- Scope (who can see this memory)
- Full memory content

## Examples

```
You: /recall "authentication" --mode approved_standards

AgentBrain: # Relevant Memories (2 found)

## 1. api_auth_decisions.md (relevance: 87% | trust: ✓ 80%)
**Scope:** project:myapi | **Source:** adr | **Status:** approved | **Tags:** security, jwt

# API Authentication Decisions

We use JWT tokens for API authentication with the following flow:
...

You: /recall "RAP handler error" --mode similar_incidents --domain-tags RAP

AgentBrain: # Relevant Memories (1 found)

## 1. incident_234.md (relevance: 92% | trust: ~ 50%)
**Scope:** team:sap_dev | **Source:** incident | **Status:** draft | **Tags:** RAP, CDS, OData

# RAP Handler Error Incident

Issue: Handler method not found in RAP service...
```

## Tips

- **Be specific** - "error handling in API routes" works better than "errors"
- **Use natural language** - Ask questions like you would to a colleague
- **Combine filters** - Use `--mode` with `--domain-tags` for precise results
- **Check trust levels** - For critical decisions, prefer memories with ✓ status
- **Follow up** - Use the memory file name to `/recall` more from that file
