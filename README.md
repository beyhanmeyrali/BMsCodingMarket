# honcho-local

> **Local-first memory and reasoning for AI agents using Ollama - no Docker, no API keys, no cloud.**

## What is honcho-local?

**honcho-local** is a local-first alternative to the [official Honcho](https://github.com/plastic-labs/honcho) cloud service. It provides the same core concepts (peers, sessions, memory, reasoning) but runs entirely on your machine using Ollama.

| Aspect | Official Honcho | honcho-local |
|--------|----------------|--------------|
| **Installation** | Docker + Postgres + migrations | Ollama only |
| **API Keys** | Required (Anthropic/OpenAI) | Not required |
| **Connectivity** | Requires internet | Works offline |
| **Storage** | Postgres database | JSON files (optional Postgres) |
| **LLM** | Cloud APIs | Local Ollama models |
| **Cost** | Pay per API call | Free (after model download) |

## Quick Overview Diagram

```mermaid
flowchart LR
    subgraph User
        Dev[Developer]
        Agent[AI Agent]
    end

    subgraph honcho_local
        Memory[Memory Storage]
        Reason[LLM Reasoning]
        Search[Semantic Search]
    end

    subgraph Outputs
        Wiki[LLM Wiki Export]
        Query[Natural Language]
    end

    Dev -->|/honcho-install| Agent
    Agent -->|Add messages| Memory
    Memory -->|Export to markdown| Wiki
    Memory -->|Ask questions| Query
    Query -->|Reasoning trace| Agent

    style Memory fill:#e3f2fd
    style Wiki fill:#f3e5f5
```

## Features

| Feature | Description |
|---------|-------------|
| **Peer Paradigm** | Treat users and agents symmetrically as "peers" |
| **Session Management** | Isolated conversation threads with full history |
| **Natural Language Queries** | Ask "What does this user typically want?" |
| **Thinking Mode** | See model's reasoning trace (qwen3.5:9b) |
| **Semantic Search** | Vector embeddings for finding similar messages |
| **Cached Representations** | User profiles that compound over time |
| **Wiki Export** | Export to markdown for browsing in Obsidian |
| **Wiki Import** | Learn from existing wiki documentation |
| **100% Local** | No cloud APIs, no API keys, works offline |

## Architecture

```mermaid
flowchart TB
    subgraph Claude_Code
        Agent[AI Agent]
        Skills[Skills]
        Cmds[Commands]
    end

    subgraph honcho_local_plugin["honcho-local Plugin"]
        Cmd1["honcho-install cmd"]
        Cmd2["honcho-check cmd"]
        Cmd3["honcho-to-wiki cmd"]
        Cmd4["wiki-to-honcho cmd"]
        Lib[local_honcho.py]
        WikiSkill[honcho-to-wiki Skill]
    end

    subgraph Local_Machine
        Ollama[Ollama Server<br/>localhost:11434]

        subgraph Models
            Chat[qwen3.5:9b<br/>Chat + Thinking]
            Emb[qwen3-embedding:0.6b<br/>Semantic Search]
        end

        Storage[JSON Storage<br/>honco_*.json]
        WikiDir[Wiki Export<br/>wiki/ folder]
    end

    Agent --> Skills
    Agent --> Cmds
    Cmd1 --> Lib
    Cmd2 --> Lib
    Cmd3 --> Lib
    Cmd4 --> Lib

    Lib --> Ollama
    Ollama --> Chat
    Ollama --> Emb

    Lib --> Storage
    Lib <-->|Bidirectional| WikiDir

    classDef local fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef ollama fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef model fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class Lib,Storage,WikiDir local
    class Ollama ollama
    class Chat,Emb model
```

> **Note:** Wiki exports can be viewed in [Obsidian](https://obsidian.md) (a knowledge base app with graph view and backlinking).

## Core Workflows

### Workflow 1: Store and Query Memory

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant Honcho as honcho-local
    participant Ollama as Ollama

    Agent->>Honcho: Add message("I need help with PO")
    Honcho->>Storage: Save to JSON
    Agent->>Honcho: What does user want?
    Honcho->>Ollama: Chat with context
    Ollama-->>Agent: "User needs PO help"
    Agent->>Honcho: Get representation
    Honcho-->>Agent: Profile with interests
```

### Workflow 2: Export to Wiki

```mermaid
flowchart LR
    A[honcho JSON] -->|Export| B[Markdown Files]
    B --> C[Peers Directory]
    B --> D[Sessions Directory]
    B --> E[index.md]
    B --> F[log.md]
    C --> G[Obsidian]
    D --> G

    style A fill:#fce4ec
    style B fill:#f3e5f5
    style G fill:#e1f5fe
```

### Workflow 3: Import from Wiki

```mermaid
flowchart LR
    A[Obsidian Vault] -->|Import| B[Markdown Files]
    B --> C[Parse Frontmatter]
    C --> D[honcho JSON]
    D --> E[Agent Memory]

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style D fill:#fce4ec
    style E fill:#e3f2fd
```

## Quick Start

### One-Time Setup (Run in Claude Code)

#### 1. Add the Marketplace

```
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
```

**If authentication fails**, clone manually first:
```bash
git clone https://github.com/beyhanmeyrali/BMsCodingMarket.git ~/claude-marketplaces/bms
```
Then add the local path:
```
/plugin marketplace add ~/claude-marketplaces/bms
```

#### 2. Install the Plugin

```
/plugin install honcho-local@bms-marketplace
```

#### 3. Install Ollama and Models

```
/honcho-install
```

This automatically:
- Downloads `qwen3.5:9b` model (~6GB)
- Downloads `qwen3-embedding:0.6b` model (~600MB)
- Installs Python dependencies

#### 4. Verify Installation

```
/honcho-check
/plugin list                           # Should show honcho-local
/plugin info honcho-local              # Shows description, version
```

### Keeping It Up to Date

```
/plugin marketplace update                              # Refresh marketplace
/plugin update honcho-local@bms-marketplace            # Update plugin
```

### 3. Use in Your Code

```python
import sys
sys.path.insert(0, "plugins/honcho-local/scripts")
from local_honcho import get_local_honcho

# Initialize with thinking mode
memory = get_local_honcho(
    workspace_id="my-agent",
    model="qwen3.5:9b",
    think=True,
)

# Create peers
user = memory.peer("user-123", name="Alice")
agent = memory.peer("bot", peer_type="agent")

# Add conversation
session = memory.session("conv-1")
session.add_messages([
    {"role": "user", "content": "I need PO approval help", "metadata": {"peer_id": user.id}},
    {"role": "assistant", "content": "I can help with that", "metadata": {"peer_id": agent.id}},
])

# Get insights with reasoning trace
result = memory.chat(user.id, "What does this user need?", include_thinking=True)
print(result["thinking"])  # Model's internal reasoning
print(result["content"])   # Final answer

# Semantic search
results = memory.search(user.id, "PO approval", limit=5)
```

### 4. Export to Wiki

```
/honcho-to-wiki
```

Creates `wiki/` folder with:
- `peers/*.md` - Entity pages for each user/agent
- `sessions/*.md` - Conversation logs
- `index.md` - Catalog of all pages
- `log.md` - Export log

Open `wiki/` in Obsidian to browse your agent's memory!

### 5. Import from Wiki

```
/wiki-to-honcho
```

Imports existing wiki markdown into honcho memory:
- Parses YAML frontmatter
- Extracts transcripts
- Builds honcho JSON storage

## Commands Reference

| Command | Purpose |
|---------|---------|
| `/honcho-install` | Install Ollama and required models |
| `/honcho-check` | Verify installation and setup |
| `/honcho-to-wiki` | Export honcho memory to wiki markdown |
| `/wiki-to-honcho` | Import wiki markdown into honcho memory |

## Data Storage

### Where Data Lives

```
your-project/
├── honcho_data/           ← All honcho storage (gitignored)
│   ├── honco_my-agent.json
│   └── honco_other-workspace.json
├── main.py
└── ...
```

**Storage location**: `honcho_data/` folder (auto-created, added to `.gitignore`)

**One JSON file per workspace** - Named `honco_{workspace_id}.json`

### Data Structure

```json
{
  "peers": {
    "workspace:user123": {
      "id": "user123",
      "name": "Alice",
      "peer_type": "user",
      "created_at": "2026-04-13T..."
    }
  },
  "sessions": {},
  "messages": {
    "workspace:conv-1": [
      {
        "id": "uuid",
        "role": "user",
        "content": "Hello",
        "timestamp": "2026-04-13T...",
        "metadata": {"peer_id": "user123"}
      }
    ]
  },
  "representations": {
    "workspace:user123:all": {
      "interests": ["topic1", "topic2"],
      "communication_style": "direct",
      "sentiment": "positive"
    }
  }
}
```

### How It Works

```mermaid
flowchart LR
    A[Agent adds message] --> B[Stored in messages array]
    B --> C[Saved to honco_*.json]
    C --> D[Query: chat user_id]
    D --> E[Loads conversation history]
    E --> F[Sends to Ollama with context]
    F --> G[Returns insights about user]
    G --> H[get_representation called]
    H --> I[Generates user profile]
    I --> J[Cached in representations]
    J --> K[Saved to JSON]

    style A fill:#e3f2fd
    style K fill:#e3f2fd
    style F fill:#fce4ec
    style I fill:#f3e5f5
```

### Knowledge Compounding

Unlike RAG which re-processes documents every query, honcho-local **caches insights**:

```python
# First interaction: LLM analyzes conversation
profile = memory.get_representation("user-123")
# Returns: {"interests": [...], "style": "direct", "sentiment": "neutral"}

# Subsequent interactions: Reads cached profile
profile = memory.get_representation("user-123")
# Returns cached result immediately (no LLM call)
```

The representation cache updates with new information, so insights **compound over time**.

## Performance

### Benchmark Results

Tested on:
- **GPU**: NVIDIA GeForce RTX 5060 Laptop GPU (8GB VRAM)
- **CPU**: AMD Ryzen AI 9 365 (10 cores, 20 threads)
- **RAM**: 32 GB
- **Ollama**: qwen3.5:9b (chat), qwen3-embedding:0.6b (search)

| Operation | Metric | Result |
|-----------|--------|--------|
| **Write** | Throughput | ~200 msg/s |
| **Write** | Latency | ~5ms per message |
| **Read** | Latency | ~8μs per context |
| **Chat** | LLM Reasoning | ~35s per query |
| **Search** | Semantic Search | ~6s per query |
| **Search** | Relevance | 100% accuracy |
| **Profile** | User Representation | ~120s (first time) |

**Notes:**
- Write/Read: JSON storage is very fast
- Chat/Profile: LLM推理 depends on model size (qwen3.5:9b)
- Search: Includes embedding generation + similarity calculation
- Profile: First run is slow, subsequent reads use cache

Run your own benchmark:
```bash
cd tests && python benchmark.py
```

## Wiki Integration

### honcho ↔ Wiki Bridge

```mermaid
flowchart LR
    subgraph honcho_local
        H1[JSON Storage]
        H2[Memory API]
    end

    subgraph wiki_export
        W1[Markdown Files]
        W2[Obsidian Viewer]
        W3[Graph View]
    end

    H2 -->|Export| W1
    W1 --> W2
    W2 --> W3
    W3 -->|Visualize connections| W1

    H1 -.->|Import new knowledge| H2

    style H1 fill:#fce4ec
    style W1 fill:#f3e5f5
    style W2 fill:#e1f5fe
```

### Export Format

```
wiki/
├── index.md              # Catalog of all pages
├── log.md                 # Export log
├── peers/
│   ├── user_123.md       # User profile
│   └── agent.md           # Agent profile
└── sessions/
    ├── conv-1.md          # Conversation log
    └── conv-2.md
```

### Wiki Page Format

**Peer pages** include:
- YAML frontmatter with metadata
- Interests and communication style
- Links to participated sessions

**Session pages** include:
- Full conversation transcript
- Participant information
- Auto-generated topics

## Components

```
honcho-local/
├── commands/
│   ├── install.md      # /honcho-install - Setup Ollama
│   ├── check.md        # /honcho-check - Verify setup
│   ├── to-wiki.md       # /honcho-to-wiki - Export to markdown
│   └── from-wiki.md    # /wiki-to-honcho - Import from markdown
├── scripts/
│   ├── local_honcho.py # Core library
│   ├── setup.py        # Installation script
│   ├── check.py        # Verification script
│   ├── to_wiki.py      # Export to wiki
│   └── wiki_to_honcho.py # Import from wiki
├── skills/
│   ├── honcho-local/   # Main honcho skill
│   │   └── SKILL.md
│   └── honcho-to-wiki/  # Wiki conversion skill
│       └── SKILL.md
├── hooks/
│   └── hooks.json      # Session hooks
└── requirements.txt    # Python dependencies
```

## Core Classes

| Class | Purpose |
|-------|---------|
| `LocalHoncho` | Main memory provider, manages workspaces |
| `Session` | Conversation thread with message history |
| `Peer` | User or agent representation |
| `Message` | Individual message with metadata |

## Key Methods

```python
# Factory function
memory = get_local_honcho(workspace_id="my-app")

# Peer management
user = memory.peer("user-id", name="User", peer_type="user")
agent = memory.peer("agent-id", name="Agent", peer_type="agent")

# Session management
session = memory.session("conversation-id")
session.add_messages([...])

# Query with thinking
result = memory.chat(peer_id, "What patterns exist?", include_thinking=True)
# Returns: {"thinking": "...", "content": "..."}

# Get profile (cached, compounds over time)
profile = memory.get_representation(peer_id)
# Returns: {"interests": [...], "communication_style": "...", ...}

# Semantic search
results = memory.search(peer_id, "query", limit=5)
# Returns: [{"content": "...", "score": 0.95}, ...]
```

## Thinking Mode

Enable thinking mode to see the model's reasoning process:

```python
memory = get_local_honcho(
    workspace_id="my-agent",
    think=True,  # or "low", "medium", "high" for GPT-OSS
)

# All major methods support include_thinking
memory.chat(user_id, question, include_thinking=True)
memory.get_representation(user_id, include_thinking=True)
session.get_context(summary=True, include_thinking=True)
```

**Supported models:**
- `qwen3.5:9b` - Recommended (fast with thinking)
- `qwen3:8b` - Smaller alternative
- `deepseek-r1` - DeepSeek's reasoning model
- `gpt-oss` - With `think="low"|"medium"|"high"`

## Storage Options

### JSON (Default) - Simple & Portable

```python
memory = get_local_honcho(workspace_id="my-app")
# Creates: honco_my-app.json in current directory
```

**Best for:** Development, testing, single-machine deployments

### Custom Path

```python
memory = LocalHoncho(
    workspace_id="my-app",
    db_path="/absolute/path/to/memory.json",
)
```

### Postgres (Optional) - Production Ready

```python
memory = get_local_honcho(
    workspace_id="my-app",
    use_postgres=True,
    postgres_uri="postgresql://user:pass@localhost/db",
)
```

**Best for:** Production, multiple processes, better performance

## Comparisons

### vs Official Honcho

| Feature | Official Honcho | honcho-local |
|---------|----------------|--------------|
| **Setup** | Docker Compose + Postgres | Ollama only |
| **Installation** | Multiple steps, migrations | One command: `/honcho-install` |
| **API Keys** | Required | Not required |
| **Internet** | Required for API calls | Only for model download |
| **Thinking** | Via cloud LLMs | Via local models |
| **Cost** | Per-API-call pricing | Free (hardware cost only) |
| **Privacy** | Data sent to cloud | 100% local |

### vs Karpathy's LLM Wiki

| Aspect | LLM Wiki | honcho-local |
|--------|----------|--------------|
| **Storage** | Markdown files in directory tree | Single JSON file per workspace |
| **Purpose** | Personal knowledge bases | AI agent memory |
| **Content** | Structured wiki pages | Conversational data |
| **Writer** | LLM writes markdown | LLM queries conversations |
| **Reader** | Human reads in Obsidian | Agent queries via API |
| **Growth** | Wiki pages link together | Cached representations |
| **Best for** | Research, note-taking, reading | User behavior, chat apps |

**Both patterns share the core insight:** Knowledge should compound over time, not be re-derived every query.

**They're complementary:**
- `honcho-local` - Agent memory and user interactions
- `LLM Wiki` - Knowledge management and documentation
- **Together** - Agents can export to wiki for human browsing

## Components Explained

 honcho-local integrates several powerful tools. Here's what each one does:

| Component | What is it? | Why use it? |
|-----------|-------------|-------------|
| **Ollama** | Local LLM runner - runs AI models on your machine | No API costs, works offline, privacy-first |
| **qwen3.5:9b** | Chat model with "thinking" capability | See the AI's reasoning process, faster responses |
| **qwen3-embedding:0.6b** | Converts text to vector numbers | Enables semantic search - find related messages |
| **Obsidian** | Knowledge base app for markdown files | Visualize connections, graph view, linked notes |
| **Mermaid** | Diagrams in markdown using code | Architecture docs rendered automatically on GitHub |
| **Honcho** | Memory library for AI agents | Track user behavior across sessions, detect patterns |
| **LLM Wiki** | Pattern for persistent AI knowledge | Knowledge that compounds over time vs. re-processing |

**How they work together:**
1. **Ollama** runs the AI models locally on your machine
2. **qwen3.5:9b** answers questions and shows its thinking
3. **qwen3-embedding** converts messages to vectors for search
4. **Obsidian** lets you browse the exported wiki with graph views
5. **Mermaid** renders diagrams directly in the README on GitHub

## Requirements

- **Ollama** running locally
- **Python 3.10+**
- **Dependencies:** `ollama`, `psycopg2-binary` (optional)

## Documentation

Full documentation in the [skill documentation](plugins/honcho-local/skills/honcho-local/SKILL.md).

## Inspiration & Attribution

This project is inspired by and builds upon:

- **[Honcho by Plastic Labs](https://github.com/plastic-labs/honcho)** - Memory library for stateful agents
- **[LLM Wiki pattern by Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** - Personal knowledge bases with LLMs
- **[Ollama](https://ollama.ai)** - Local LLM inference engine

The honcho-local implementation provides:
- Local-first alternative to Honcho's cloud service
- Wiki export compatible with Karpathy's LLM Wiki pattern
- Bidirectional bridge between agent memory and human-readable wiki

## License

MIT License

## Author

Beyhan Meyrali - [beyhanmeyrali@gmail.com](mailto:beyhanmeyrali@gmail.com)
