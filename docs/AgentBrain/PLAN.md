# AgentBrain - Implementation Plan

> **Status:** Ready for Phase 0
> **Created:** 2025-04-15
> **Author:** Beyhan Meyrali
> **Location:** `BMsCodingMarket/plugins/agentbrain/`

---

## Architectural Decisions (Finalized)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Distribution** | Plugin in BMsCodingMarket | Marketplace model, easy install |
| **Vector DB** | Qdrant with Docker | Purpose-built, great filter perf, easy setup |
| **Hooks language** | Python | Transparent, auditable, no binary trust issues |
| **MEMORY.md** | Generated index from actual files | Single source of truth, no merge conflicts |
| **Multi-tenant** | Shared Qdrant with scope filters | One infra, impossible cross-scope leakage |
| **Embeddings** | Qwen3-0.6B via Ollama (default) | Local, free, configurable |
| **Curation** | Subagents for judgment, scripts for mechanics | Async, don't block UX |

---

## Plugin Structure

```
BMsCodingMarket/plugins/agentbrain/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
├── hooks.json                   # Hook registration
├── docker/
│   └── qdrant-compose.yml       # Qdrant Docker Compose
├── hooks/
│   ├── session-start.py         # Regenerate index + query + inject
│   ├── user-prompt-submit.py    # On-demand recall
│   ├── stop.py                  # Spawn curator subagent
│   └── subagent-stop.py         # Process candidate memories
├── skills/
│   ├── recall/
│   │   ├── SKILL.md
│   │   └── command.md
│   ├── remember/
│   │   ├── SKILL.md
│   │   └── command.md
│   ├── forget/
│   │   ├── SKILL.md
│   │   └── command.md
│   ├── promote/
│   │   ├── SKILL.md
│   │   └── command.md
│   ├── extract-pr/
│   │   ├── SKILL.md
│   │   └── command.md
│   └── memory-stats/
│       ├── SKILL.md
│       └── command.md
├── agents/
│   ├── memory-curator.md        # Summarize + categorize + dedup
│   ├── memory-extractor.md      # PR/incident/ADR import
│   └── memory-reviewer.md       # Staleness sweep
├── scripts/
│   ├── regenerate_index.py      # Generate MEMORY.md from files
│   ├── embed.py                 # Generate embeddings via Ollama
│   ├── upsert.py                # Write to Qdrant
│   ├── query.py                 # Scoped vector search
│   ├── decay.py                 # Staleness sweep (cron)
│   ├── seed_memories.py         # One-off: embed existing memories
│   └── providers/
│       ├── qdrant.py            # Qdrant client wrapper
│       ├── ollama.py            # Ollama embedding client
│       └── base.py              # Provider interface
└── tests/
    ├── test_qdrant.py
    ├── test_embed.py
    └── test_query.py
```

---

## Configuration (.env.example)

```bash
# =============================================================================
# AgentBrain Configuration
# Copy to your project root as .agentbrain.env or set as environment variables
# =============================================================================

# -----------------------------------------------------------------------------
# Vector DB (Shared Qdrant for enterprise)
# -----------------------------------------------------------------------------
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=                    # Optional: for auth in production
QDRANT_COLLECTION=agentbrain_memories
QDRANT_TIMEOUT_SECONDS=10

# -----------------------------------------------------------------------------
# Embedding Model (Local Ollama)
# -----------------------------------------------------------------------------
EMBEDDING_MODEL=qwen3:0.6b         # Options: qwen3:0.6b, nomic-embed-text, bge-small
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_DIMENSION=768            # qwen3:0.6b = 768, nomic = 768, bge-small = 384
EMBEDDING_TIMEOUT_SECONDS=30

# -----------------------------------------------------------------------------
# Scope (Auto-detected from git, but can override)
# -----------------------------------------------------------------------------
AGENTBRAIN_SCOPE=user              # Scope: user|team|project|org
AGENTBRAIN_TEAM_ID=                # For team memories (e.g., "platform")
AGENTBRAIN_ORG_ID=                 # For org-wide policies (e.g., "acme")

# -----------------------------------------------------------------------------
# Memory Settings
# -----------------------------------------------------------------------------
MEMORY_DIR=~/.claude/memory
MEMORY_INDEX_MAX_LINES=150
RETRIEVAL_TOP_K=8
RETRIEVAL_MIN_SCORE=0.6

# -----------------------------------------------------------------------------
# Curator Settings
# -----------------------------------------------------------------------------
CURATOR_MODEL=sonnet               # Model for subagent: sonnet|haiku
CURATOR_TIMEOUT_SECONDS=300
CURATOR_AUTO_RUN=true              # Auto-curate on session end

# -----------------------------------------------------------------------------
# Privacy & Safety
# -----------------------------------------------------------------------------
AGENTBRAIN_PRIVACY_ENABLED=true
AGENTBRAIN_REDACT_SECRETS=true     # Auto-detect API keys, tokens
AGENTBRAIN_ALLOWED_PATTERNS=       # Regex allow-list for content
```

---

## Qdrant Collection Schema

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

client.create_collection(
    collection_name="agentbrain_memories",
    vectors_config=VectorParams(
        size=768,  # Qwen3-0.6B embedding dimension
        distance=Distance.COSINE,
    ),
    payload_schema={
        "file_path": PayloadSchemaType.KEYWORD,
        "scope": PayloadSchemaType.KEYWORD,      # user:bob, team:platform, etc.
        "type": PayloadSchemaType.KEYWORD,       # user, feedback, project, reference
        "created_at": PayloadSchemaType.INTEGER,
        "updated_at": PayloadSchemaType.INTEGER,
        "provenance_weight": PayloadSchemaType.FLOAT,  # ADR=1.0, PR=0.8, personal=0.5
        "source": PayloadSchemaType.KEYWORD,     # adr, pr, incident, session, manual
        "author": PayloadSchemaType.KEYWORD,
        "git_commit": PayloadSchemaType.KEYWORD,
        "workspace": PayloadSchemaType.KEYWORD,  # For multi-workspace isolation
        "embedding_model": PayloadSchemaType.KEYWORD,  # For reindexing
        "access_count": PayloadSchemaType.INTEGER,
        "thumbs_up": PayloadSchemaType.INTEGER,
        "thumbs_down": PayloadSchemaType.INTEGER,
        "pinned": PayloadSchemaType.BOOL,
        "ttl": PayloadSchemaType.INTEGER,        # Unix timestamp for expiry
    }
)
```

---

## Memory File Format

### Memory Body File (e.g., `user_preferences.md`)

```markdown
---
name: user-preferences
description: User coding preferences and workflow habits
type: user
scope: user:bob
created_at: 2025-04-15T10:30:00Z
updated_at: 2025-04-15T10:30:00Z
source: session
author: bob@acme.com
provenance_weight: 0.5
tags: [typescript, testing, vim]
---

# User Preferences

## Coding Style
- Prefers TypeScript strict mode for all new projects
- Uses functional components over class components
- Favors composition over inheritance

## Editor & Workflow
- Uses Neovim with TypeScript plugin
- Runs tests before committing
- Prefers concise answers over explanations

## Tech Stack
- Frontend: TypeScript, React, Tailwind
- Backend: Python, FastAPI, PostgreSQL
- Infrastructure: Docker, Kubernetes
```

### MEMORY.md (Generated Index)

```markdown
# Memory Index

> Generated by AgentBrain. Do not edit manually.
> Last updated: 2025-04-15T14:30:00Z

## User Memories

- [User Preferences](user_preferences.md) — Coding style, editor workflow, tech stack
- [Testing Habits](testing_habits.md) — Tests before commit, prefers pytest

## Feedback

- [Use TDD](feedback_tdd.md) — **Why:** User confirmed this works well for their workflow
- [Concise Answers](feedback_concise.md) — **Why:** User prefers terse responses

## Project: agentbrain

- [Qdrant Decision](project_qdrant.md) — Chose Qdrant over pgvector for filter performance
```

---

## Phase 0: Foundation MVP

**Goal:** Prove retrieval works with Qdrant + local embeddings

### Scope

```
✓ plugin.json with manifest
✓ .env.example with all config
✓ requirements.txt
✓ docker/qdrant-compose.yml
✓ SessionStart hook (regenerate + query + inject)
✓ Qdrant provider client
✓ Ollama embedding provider
✓ query.py (scoped search)
✓ embed.py (generate embeddings)
✓ upsert.py (write to Qdrant)
✓ seed_memories.py (one-off import)
✗ No curator yet (manual memory writes)
✗ No skills yet (just automatic retrieval)
```

### SessionStart Hook Flow

```python
# hooks/session-start.py

import os
import sys
from pathlib import Path

# Add plugin scripts to path
plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
sys.path.insert(0, str(plugin_root / 'scripts'))

from providers.qdrant import QdrantProvider
from providers.ollama import OllamaEmbedder
from regenerate_index import regenerate_memory_index
from query import query_memories
from injector import inject_into_context

def main():
    # 1. Regenerate MEMORY.md index (always fresh, ~50ms)
    regenerate_memory_index()

    # 2. Get current context
    workspace = os.environ.get('AGENTBRAIN_WORKSPACE', 'default')
    repo_path = get_git_repo_path()
    user_id = os.environ.get('USER', os.environ.get('USERNAME'))
    allowed_scopes = compute_allowed_scopes(user_id, repo_path)

    # 3. Query shared Qdrant with scope filter
    memories = query_memories(
        query="current context",  # Or embed recent prompts
        scopes=allowed_scopes,
        top_k=8
    )

    # 4. Inject into system prompt
    if memories:
        inject_into_context(memories)

    return memories

def compute_allowed_scopes(user_id, repo_path):
    """Compute allowed scopes based on user and repo."""
    scopes = [f"user:{user_id}"]

    # Add team scope if configured
    if team_id := os.environ.get('AGENTBRAIN_TEAM_ID'):
        scopes.append(f"team:{team_id}")

    # Add project scope if in a git repo
    if repo_path:
        repo_name = get_repo_name(repo_path)
        scopes.append(f"project:{repo_name}")

    # Add org scope if configured
    if org_id := os.environ.get('AGENTBRAIN_ORG_ID'):
        scopes.append(f"org:{org_id}")

    return scopes

if __name__ == "__main__":
    main()
```

### Scripts to Implement

#### `scripts/providers/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Memory:
    file_path: str
    scope: str
    type: str  # user, feedback, project, reference
    content: str
    embedding: Optional[List[float]] = None
    metadata: dict = None

class VectorDBProvider(ABC):
    @abstractmethod
    def upsert(self, memory: Memory) -> str:
        """Write or update memory, return ID."""
        pass

    @abstractmethod
    def query(self, embedding: List[float], scopes: List[str], top_k: int = 8) -> List[Memory]:
        """Query with scope filter."""
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete memory by ID."""
        pass

class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
```

#### `scripts/providers/qdrant.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny
from .base import VectorDBProvider, Memory
import time

class QdrantProvider(VectorDBProvider):
    def __init__(self, host="localhost", port=6333, collection="agentbrain_memories"):
        self.client = QdrantClient(host=host, port=port)
        self.collection = collection
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if not exists."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def upsert(self, memory: Memory) -> str:
        """Write or update memory."""
        import hashlib
        memory_id = hashlib.md5(memory.file_path.encode()).hexdigest()

        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(
                id=memory_id,
                vector=memory.embedding,
                payload={
                    "file_path": memory.file_path,
                    "scope": memory.scope,
                    "type": memory.type,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                    **(memory.metadata or {})
                }
            )]
        )
        return memory_id

    def query(self, embedding, scopes: List[str], top_k: int = 8) -> List[Memory]:
        """Query with mandatory scope filter."""
        results = self.client.search(
            collection_name=self.collection,
            query_vector=embedding,
            query_filter=Filter(
                must=[FieldCondition(
                    key="scope",
                    match=MatchAny(any=scopes)
                )]
            ),
            limit=top_k,
            with_payload=True
        )

        return [
            Memory(
                file_path=r.payload.get("file_path"),
                scope=r.payload.get("scope"),
                type=r.payload.get("type"),
                content="",  # Load from file
                metadata=r.payload
            )
            for r in results
        ]

    def delete(self, memory_id: str) -> bool:
        """Delete memory by ID."""
        try:
            self.client.delete(
                collection_name=self.collection,
                points_selector=[memory_id]
            )
            return True
        except Exception:
            return False
```

#### `scripts/providers/ollama.py`

```python
import requests
from typing import List
from .base import EmbeddingProvider

class OllamaEmbedder(EmbeddingProvider):
    def __init__(self, base_url="http://localhost:11434", model="qwen3:0.6b"):
        self.base_url = base_url
        self.model = model
        self._check_available()

    def _check_available(self):
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Ollama not available at {self.base_url}: {e}")

    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("embedding", [])

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
```

#### `scripts/regenerate_index.py`

```python
import os
import re
import yaml
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".claude"memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"
MAX_LINES = 150

def parse_frontmatter(file_path):
    """Extract YAML frontmatter from markdown."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
    except Exception:
        pass
    return {}

def generate_index():
    """Generate MEMORY.md from all memory files."""
    if not MEMORY_DIR.exists():
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    memory_count = 0

    for md_file in MEMORY_DIR.glob("*.md"):
        if md_file.name == "MEMORY.md":
            continue

        meta = parse_frontmatter(md_file)
        if meta and 'name' in meta:
            memory_type = meta.get('type', 'other')
            title = meta['name']
            description = meta.get('description', '')[:100]
            rel_path = md_file.name

            entries.append(f"### {memory_type.capitalize()}\n")
            entries.append(f"- [{title}]({rel_path}) — {description}\n")
            memory_count += 1

        if memory_count >= MAX_LINES:
            break

    content = f"""# Memory Index

> Generated by AgentBrain. Do not edit manually.
> Last updated: {datetime.now().isoformat()}
> Total memories: {memory_count}

"""
    content += "\n".join(entries)

    INDEX_FILE.write_text(content, encoding='utf-8')
    print(f"Generated index with {memory_count} memories")

if __name__ == "__main__":
    generate_index()
```

---

## Phase 1: Auto-Curation

**Goal:** Sessions automatically generate curated memories

### Scope

```
✓ Stop hook (spawn curator subagent)
✓ SubagentStop hook (process candidates)
✓ memory-curator.md (subagent definition)
✓ Candidates pipeline (JSON structure)
✓ Memory file generation
✓ Embed + upsert on new memories
```

### Curator Subagent Prompt

```markdown
---
name: memory-curator
description: Extract and curate memories from session transcripts
when_to_use: Spawned by Stop hook after session ends
---

# Memory Curator

You are a memory curation subagent. Your job is to extract meaningful memories from session transcripts.

## Input

- Session transcript (full conversation)
- Current MEMORY.md index

## Process

1. **Extract candidates**: Look for:
   - User preferences explicitly stated
   - Technical decisions made
   - Bug fixes and their solutions
   - Architecture discussions
   - Workflow patterns

2. **Classify each candidate** by type:
   - `user`: Information about the user (role, preferences, knowledge)
   - `feedback`: Guidance on how to work with this user
   - `project`: Project-specific decisions, architecture, gotchas
   - `reference`: Links to external resources, docs, tools

3. **Deduplication**: Check if similar memory already exists
   - If similar exists with >0.9 similarity → skip
   - If similar exists with 0.7-0.9 → update existing
   - If no similar → create new

4. **Emit structured JSON**:

```json
{{
  "memories": [
    {{
      "action": "create|update|skip",
      "file": "user_preferences.md",
      "type": "user",
      "scope": "user:bob",
      "frontmatter": {{
        "name": "User Preferences",
        "description": "Coding style and workflow habits",
        "type": "user",
        "scope": "user:bob",
        "source": "session"
      }},
      "content": "# User Preferences\n\n..."
    }}
  ]
}}
```

## Guidelines

- **Be selective**: Not everything is a memory. Capture what would be useful NEXT time.
- **Be specific**: "User likes TypeScript" → "User requires TypeScript strict mode for all projects"
- **Be concise**: Memory files should be readable. Use bullets, headers, tables.
- **Respect scope**: Personal = auto-write, team/project = suggest promotion
```

### Stop Hook

```python
# hooks/stop.py

import os
import subprocess
import json
from pathlib import Path

def spawn_curator_subagent(transcript_path):
    """Spawn memory-curator subagent with session transcript."""
    plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))

    # Read transcript
    with open(transcript_path) as f:
        transcript = f.read()

    # Prepare subagent prompt
    prompt = f"""
# Session Transcript

{transcript}

# Task

Extract and curate memories from this session. Output JSON as specified in memory-curator.md.
"""

    # Write to temp file for subagent
    temp_file = plugin_root / ".curator_prompt.txt"
    temp_file.write_text(prompt)

    # The subagent will be spawned by CC
    # We just signal that curation is needed
    return temp_file

if __name__ == "__main__":
    # Get transcript from env or arg
    transcript_path = os.environ.get('CLAUDE_TRANSCRIPT_PATH')
    if transcript_path:
        spawn_curator_subagent(transcript_path)
```

---

## Phase 2: User-Facing Skills

**Goal:** Explicit user control over memory

### Skills to Implement

#### `/recall` - Semantic Memory Search

```markdown
---
name: recall
description: Search your memory by semantic meaning
---

# Recall Memory

Search your stored memories by meaning, not just keywords.

## Usage

```
/recall "how do we handle authentication"
/recall "typescript configuration"
/recall "testing conventions"
```

## What Happens

1. Embeds your query
2. Searches Qdrant with your allowed scopes
3. Returns relevant memories with their content
```

#### `/remember` - Explicit Memory Storage

```markdown
---
name: remember
description: Explicitly store a fact to memory
---

# Remember

Store a fact, preference, or decision to memory.

## Usage

```
/remember "We use Qdrant for vector storage"
/remember "Team prefers functional components"
```

## What Happens

1. Creates memory file with appropriate type
2. Generates embedding
3. Upserts to Qdrant
4. Updates MEMORY.md index
```

#### `/forget` - Delete Memory

```markdown
---
name: forget
description: Remove a stored memory
---

# Forget

Remove a memory from storage.

## Usage

```
/forget <memory-id>
/forget "user_preferences"
```

## What Happens

1. Deletes from Qdrant
2. Deletes markdown file
3. Regenerates MEMORY.md index
```

---

## Phase 3: Team Layer

**Goal:** Shared team and project memories

### Scope

```
✓ .agentbrain/ directory in repos
✓ Team memory files in repo (versioned)
✓ Team scope queries
✓ Promotion workflow (personal → team)
```

### Repo Structure

```
acmo/service-a/
├── .agentbrain/
│   ├── config.yml              # Team config override
│   └── memory/
│       ├── team_conventions.md
│       └── api_design_decisions.md
├── src/
└── README.md
```

### Config File

```yaml
# .agentbrain/config.yml
team_id: platform
org_id: acme
memory_types:
  - team
  - project
review_required: true          # PR required for team memories
codeowners: ["@platform-team"]
```

---

## Phase 4: Extractors

**Goal:** Import knowledge from existing sources

### Extractors to Build

1. **PR Extractor** - Pull review comments as conventions
2. **ADR Extractor** - Import Architecture Decision Records
3. **Incident Extractor** - Parse postmortems for "never do X" rules
4. **Slack Extractor** (opt-in) - Tribal knowledge from resolved threads

---

## Phase 5: Governance

**Goal:** Memory health, lifecycle, promotion

### Features

- **Promotion workflow** - personal → team → project → org
- **Decay sweep** - Flag stale memories
- **Stats dashboard** - Hit rate, usage metrics
- **Review queue** - Memories awaiting promotion

---

## Installation Instructions (for Users)

```bash
# 1. Install the plugin
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install agentbrain@bms-marketplace

# 2. Start Qdrant
docker-compose -f ~/.claude/plugins/agentbrain/docker/qdrant-compose.yml up -d

# 3. Start Ollama (if not running)
ollama serve

# 4. Pull embedding model
ollama pull qwen3:0.6b

# 5. Configure .env
cp ~/.claude/plugins/agentbrain/.env.example ~/.agentbrain.env
# Edit ~/.agentbrain.env with your settings

# 6. Seed existing memories (optional)
python ~/.claude/plugins/agentbrain/scripts/seed_memories.py
```

---

## Dependencies

```txt
# requirements.txt
qdrant-client>=1.12.0
requests>=2.31.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
ollama>=0.1.0  # Optional: for direct Ollama integration
```

---

## Testing Strategy

```python
# tests/test_qdrant.py
def test_qdrant_upsert():
    """Test writing to Qdrant."""

def test_qdrant_query_with_scope():
    """Test scope filtering."""

# tests/test_embed.py
def test_ollama_embedding():
    """Test embedding generation."""

# tests/test_query.py
def test_end_to_end_query():
    """Test full retrieval flow."""
```

---

## Open Questions for Development

1. **Subagent communication** - How does curator subagent output get back to hooks? JSON file? Stdout?
2. **Transcript capture** - How does Stop hook access session transcript?
3. **Windows path handling** - Ensure all paths work on Windows/Mac/Linux
4. **Error handling** - What if Qdrant is down? Graceful degradation?
5. **Migration path** - How to handle embedding model changes?

---

## Next Actions

1. ✅ Create documentation (this file + IDEA.md)
2. **Phase 0 Implementation**:
   - [ ] Create plugin.json
   - [ ] Set up project structure
   - [ ] Implement Qdrant provider
   - [ ] Implement Ollama embedder
   - [ ] Implement SessionStart hook
   - [ ] Test retrieval end-to-end

3. **After Phase 0**:
   - [ ] Implement curator subagent
   - [ ] Implement Stop/SubagentStop hooks
   - [ ] Build user-facing skills
   - [ ] Add team layer
