---
name: use-honcho-locally
description: Use when building AI agents that need persistent memory across sessions. Official Honcho memory library running 100% locally with Ollama (no API keys) and Docker Postgres. This skill tells Claude Code how to initialize Honcho, create peers/sessions/messages, and query user behavior - all running locally on the user's machine. Triggers: agent needs memory, remember user across sessions, persistent user data, track user preferences, conversation history storage, agent memory system, user behavior analysis, maintain user context, local llm memory, offline agent memory.
---

# Using Honcho Locally with Ollama

**Official Honcho memory system - 100% local with Ollama, no API keys required.**

## Quick Start

```python
from honcho import Honcho

# Initialize with local Honcho server
honcho = Honcho(
    workspace_id="my-agent",
    base_url="http://localhost:8000"  # Your local Honcho server
)

# Create peers
user = honcho.peer("user-123", name="Beyhan")
agent = honcho.peer("assistant", name="AI Agent")

# Create session and add messages
session = honcho.session("conv-1")
session.add_messages([
    user.message("I need help with Python async"),
    agent.message("I can help with async/await patterns"),
])

# Query user behavior
response = user.chat("What does this user need help with?")
print(response.content)  # "The user is learning Python async programming..."
```

## Local Setup (One-Time)

### Prerequisites

```bash
# 1. Ollama (Local LLM)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:9b
ollama serve

# 2. Postgres with pgvector (Docker)
docker run -d \
  --name honcho-postgres \
  -e POSTGRES_PASSWORD=honcho123 \
  -e POSTGRES_DB=honcho_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 3. Honcho Server
git clone https://github.com/plastic-labs/honcho.git
cd honcho
cp .env.template .env

# Edit .env:
# DB_CONNECTION_URI=postgresql+psycopg://postgres:honcho123@localhost:5432/honcho_db
# LLM_OPENAI_API_BASE=http://localhost:11434/v1
# LLM_OPENAI_API_KEY=sk-placeholder
# EMBEDDING_PROVIDER=openai
# EMBEDDING_MODEL=qwen3-embedding:0.6b

# Install and run
pip install honcho-ai
uv run alembic upgrade head
uv run fastapi dev src/main.py
```

### Using with Ollama

Ollama provides an **OpenAI-compatible API** at `http://localhost:11434/v1`. Configure Honcho to use it:

```python
# In your code, Honcho uses the server's configuration
honcho = Honcho(workspace_id="my-app")

# The server handles Ollama communication
# Just use the normal Honcho API!
```

## Core Concepts

### The Peer Paradigm

Both users AND agents are "peers":

```python
# User peer
user = honcho.peer("user-123")

# Agent peer (also a peer!)
agent = honcho.peer("my-agent")

# Multi-participant sessions
session = honcho.session("team-discussion")
session.add_messages([
    user.message("I think we should use Postgres"),
    agent.message("Good choice for vector search"),
    honcho.peer("dev-lead").message("I agree, it scales well"),
])
```

### Sessions & Messages

```python
session = honcho.session("ticket-45678")

# Add messages from any peer
session.add_messages([
    user.message("PO approval is stuck"),
    agent.message("Checking status..."),
])

# Get context for LLM
context = session.context(summary=True, tokens=5000)
# Returns formatted context with recent messages + summary
```

### Natural Language Queries

```python
# Ask about a peer in plain English
response = user.chat("What's the user's main concern?")
# Returns: "The user is worried about PO approval workflow delays"

response = user.chat("What's their communication style?")
# Returns: "Direct, technical, prefers brief answers"
```

### Search

```python
# Semantic search across conversations
results = user.search("PO approval", limit=5)
# Returns messages about PO approvals, ranked by relevance

# Session-scoped search
results = session.search("database", limit=3)
```

## Common Patterns

### Pattern 1: Personalized Agent Responses

```python
def get_agent_response(user_id: str, user_message: str) -> str:
    honcho = Honcho(workspace_id="support-bot")
    user = honcho.peer(user_id)

    # Get user context
    context = user.chat("What context should I know about this user?")

    # Build prompt with context
    prompt = f"""User context: {context}

User message: {user_message}

Provide a helpful response:"""

    # Send to Ollama (via Honcho's configured LLM)
    return agent.message(prompt)  # Honcho handles LLM call
```

### Pattern 2: Cross-Session Memory

```python
# Session 1: User expresses preference
session1.add_messages([
    user.message("I prefer concise answers, no fluff"),
])

# Session 2 (days later): Agent remembers
context = user.chat("How should I respond to this user?")
# Agent knows: "Be concise and direct"
```

### Pattern 3: Multi-Agent Coordination

```python
# Create multiple agent peers
sales_agent = honcho.peer("sales-bot")
support_agent = honcho.peer("support-bot")

# Both can access the same user knowledge
user_context = sales_agent.chat("What's this user's status?")
# Both agents know the full user history
```

## Data Model

```
Workspace (my-app)
├── Peers
│   ├── user-123
│   ├── sales-bot
│   └── support-bot
├── Sessions
│   ├── conv-1 (user-123 + sales-bot)
│   └── conv-2 (user-123 + support-bot)
└── Messages (in each session)
```

## Configuration Reference

| Environment Variable | Purpose | Example |
|---------------------|---------|---------|
| `DB_CONNECTION_URI` | Postgres database | `postgresql+psycopg://...` |
| `LLM_OPENAI_API_BASE` | Ollama endpoint | `http://localhost:11434/v1` |
| `LLM_OPENAI_API_KEY` | Placeholder for Ollama | `sk-placeholder` |
| `EMBEDDING_PROVIDER` | Embedding backend | `openai` |
| `EMBEDDING_MODEL` | Embedding model | `qwen3-embedding:0.6b` |

## Troubleshooting

**"Ollama connection failed"**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

**"Postgres connection failed"**
```bash
# Check Docker container
docker ps | grep honcho-postgres

# Check logs
docker logs honcho-postgres
```

**"Module 'honcho' not found"**
```bash
pip install honcho-ai
```

## Best Practices

1. **One workspace per application** - Keeps data isolated
2. **Use descriptive peer IDs** - Easier to query later
3. **Add messages in batches** - More efficient than one-by-one
4. **Use summaries for long sessions** - Saves tokens
5. **Query before responding** - Get user context first

## Additional Resources

- Official Honcho: https://github.com/plastic-labs/honcho
- Ollama: https://ollama.com
- Wiki export/import: See `/skill: honcho-wiki`

## Author

Beyhan MEYRALI - MIT License
