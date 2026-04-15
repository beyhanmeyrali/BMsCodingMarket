# AgentBrain - Enterprise Agent Memory

> **Status:** Brainstorming Phase
> **Created:** 2025-04-15
> **Author:** Beyhan Meyrali

---

## The Vision

An enterprise-grade, persistent memory system for Claude Code that enables teams of developers to share knowledge, conventions, and context across sessions and projects. Think of it as "collective brain" for your entire engineering organization.

### The Problem

Today, Claude Code's memory is **single-tenant**:
- Each developer has their own `~/.claude/memory/`
- Each project has its own `CLAUDE.md`
- Teams can't share learned conventions
- When someone leaves, their knowledge walks away
- New team members relearn the same lessons

In a big software company with many teams, projects, and developers using Claude Code:
- Team A figures out "we always use TypeScript strict mode"
- Team B struggles with the same decision 6 months later
- Senior dev's debugging insights are lost after they close their session
- On-call runbooks exist in Confluence, not in Claude's context

### The Solution

**AgentBrain** = A Claude Code plugin that adds:

1. **Persistent memory** - Sessions end, learnings remain
2. **Shared knowledge** - Team and project-level memory layers
3. **Semantic retrieval** - Vector DB finds relevant memories automatically
4. **Auto-curation** - Subagents summarize, categorize, and dedup
5. **100% self-hosted** - Your data, your infra, free/OSS tools only

---

## Core Architecture Decisions

### 1. Plugin Model - Not MCP

**Decision:** Pure Claude Code plugin (skills + hooks + scripts + subagents)

**Why:**
- No MCP complexity
- Transparent Python scripts (no binaries)
- Works with CC's native memory system
- Can be distributed via marketplace

### 2. Memory Storage - Markdown First, Vector Index

**Decision:** Markdown files are source of truth, Vector DB is the index

```
~/.claude/memory/
├── MEMORY.md              # Generated index (always loaded)
├── user_preferences.md    # User memories
├── feedback_*.md          # Corrections/confirmations
└── project_*.md           # Project-specific

<repo>/.agentbrain/memory/
├── team_conventions.md    # Team-level (versioned with code)
└── architecture_decisions.md
```

**Why:**
- Human-readable and editable
- Git-friendly
- Works with CC's existing memory model
- Vector DB adds semantic search without replacing anything

### 3. Multi-Tenant - Shared Vector DB with Scope Filters

**Decision:** Single Qdrant instance with payload-based access control

**Scopes:**
```
user:bob          # Personal memories, only Bob sees
team:platform     # Platform team conventions, team members see
project:acme/api  # API project decisions, anyone working in repo sees
org:acme          # Company-wide policies, everyone sees
```

**Why:**
- One infra to run
- Impossible to leak between scopes (filter runs before retrieval)
- Supports personal → team → org promotion workflow

### 4. Embeddings - Local Small Models via Ollama

**Decision:** Qwen3-Embedding-0.6B by default, .env configurable

**Options:**
| Model | Size | Speed | Quality | Runtime |
|-------|------|-------|---------|---------|
| Qwen3-Embedding-0.6B | ~1.2GB | ~80ms | Top-tier | Ollama |
| nomic-embed-text v1.5 | ~270MB | ~40ms | Very good | Ollama |
| BGE-small-en-v1.5 | ~130MB | ~30ms | Good | ONNX |
| all-MiniLM-L6-v2 | ~80MB | ~20ms | Baseline | ONNX |

**Why:**
- Free after initial model download
- Works offline
- No API keys, no per-token costs
- Easy to swap in .env

### 5. Curation - Subagents for Judgment, Scripts for Mechanics

**Decision:**
- **Subagents** (Sonnet/Haiku): Summarize, categorize, dedup
- **Scripts** (Python): Embed, upsert, query, decay

**Why:**
- Summarization needs LLM judgment
- Mechanical work should be fast and deterministic
- Subagents can run async (don't block UX)

---

## The Hard Problems We're Solving

### 1. Scoping & Access Control

**Problem:** Team A's memory must not leak into Team B's agent

**Solution:** Mandatory scope filter before ANY vector search
```python
query_filter={
    "must": [
        {"key": "scope", "match": {"any": allowed_scopes}}
    ]
}
```

### 2. Trust & Provenance

**Problem:** A VP's ADR outranks a random Slack comment

**Solution:** Every memory has provenance metadata
```python
{
    "provenance_weight": 1.0,  # ADR=1.0, PR=0.8, personal=0.5
    "source": "adr",           # adr, pr, incident, slack, session
    "author": "alice@acme.com",
    "git_commit": "abc123"     # For staleness detection
}
```

Retrieval reranks by: `provenance_weight × similarity × recency_decay`

### 3. Conflict Resolution

**Problem:** Two teams have opposite conventions

**Solution:** Scope-based retrieval wins
- Agent in `acmo/team-a/*` repo sees team-a's conventions first
- Team-b conventions never appear because scope doesn't match

### 4. Write Governance

**Problem:** If everyone writes, memory becomes noise

**Solution:** Promotion path with validation
```
Personal (auto-write, no review)
  ↓ (frequently retrieved + human approve)
Team (PR-based, CODEOWNERS reviews)
  ↓ (team consensus)
Project (lives in repo, versioned with code)
  ↓ (platform team approval)
Org (policies only, locked down)
```

### 5. Staleness & Decay

**Problem:** Memory references code that was refactored/deleted

**Solution:**
- Git-aware decay: when file at `git_commit` is gone, memory is flagged
- TTL per memory type
- Thumbs up/down from actual usage
- Background sweeper (cron)

### 6. Privacy & Compliance

**Problem:** Secrets/PII must never enter memory

**Solution:**
- Pre-write scanner: regex for API keys, tokens, passwords
- PII detection: Presidio for emails, phone numbers, SSN
- Allow-list of storable content
- GDPR right-to-forget: tombstone + re-embed neighbors

---

## Prior Art & Competitive Analysis

| Project | What They Do | Gap AgentBrain Fills |
|---------|--------------|---------------------|
| **Mem0** | User-centric memory, hosted + OSS | No enterprise namespacing, not CC-native |
| **Letta/MemGPT** | OS-like memory hierarchy for one agent | Single-agent, not multi-team |
| **Zep/Graphiti** | Temporal knowledge graph | Heavyweight, not CC-integrated |
| **Cursor rules** | Static `.cursorrules` | No retrieval, no sharing, no provenance |
| **Claude Code CLAUDE.md** | Per-repo markdown, per-user memory | Single-tenant, no team layer, no retrieval |
| **Honcho** | Local memory with deriver | Not optimized for CC workflow |

### Our Wedge

**Claude-Code-native + layered-namespace + provenance-first + local-first**

Nobody else sits at this intersection.

---

## The Ecosystem Vision

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Enterprise                                  │
│                     (Platform Team Only)                            │
│              Security policies, compliance rules                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────────┐
│                         Team                                        │
│                   (Team Members)                                    │
│          Coding conventions, review standards, playbooks            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────────┐
│                       Project/Repo                                  │
│                    (Anyone in repo)                                 │
│         Architecture decisions, gotchas, invariants                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────────┐
│                       Personal                                      │
│                      (Just you)                                     │
│            Preferences, in-flight work, context                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Flows:**
- Auto-capture from sessions → personal layer
- Frequently retrieved personal memories → suggest promotion
- PR-based review → promote to team
- Team consensus → promote to project
- Platform approval → promote to org

---

## Open Questions to Resolve

1. **Monorepo vs polyrepo scoping** — Memory keyed on path? repo? team ownership file?
2. **Cross-repo reasoning** — Agent in service-A needs convention from shared lib-X
3. **LLM-extracted memory trust** — Human-curated or auto?
4. **Versioning** — Memory written against commit abc may be wrong after refactor
5. **Latency budget** — Every prompt round-trips to memory?
6. **Composition with CLAUDE.md** — Replace, augment, or sync?
7. **Offboarding** — Dev leaves → personal memories: delete, archive, or team-owned?
8. **Multi-tenant isolation** — Per-tenant collections or shared with metadata filter?

---

## Success Metrics

- **Onboarding time** — New dev productive in <1 day (down from 2 weeks)
- **Duplicate decisions** — Same debate doesn't happen twice
- **Memory hit rate** — >70% of sessions retrieve relevant memory
- **Adoption** — >50% of engineers using it within 3 months
- **Quality** — Thumbs up > thumbs down 3:1

---

## References

- **Parent Marketplace:** `E:\workspace\BMsCodingMarket`
- **Reference Plugin:** `plugins/honcho-bridge/`
- **Related:** Honcho local memory, Mem0, Zep, Claude Code memory system
