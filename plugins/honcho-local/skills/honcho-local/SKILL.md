---
name: honcho-local
description: Use when building AI agents that need to remember user behavior across sessions, detect patterns in user interactions, or provide personalized responses based on conversation history. Use when simple chat history is insufficient and agents need to reason about user preferences, communication styles, or recurring topics. Triggers: build agent with memory, remember user across sessions, persistent user data, detect user patterns, personalized agent responses, cross-session memory, track user preferences, conversation history storage, agent memory system, user behavior analysis, maintain user context.
---

# Honcho Local - Memory & Reasoning for AI Agents

**Local-first alternative to Honcho cloud service - uses Ollama instead of paid APIs.**

## Overview

**Local Honcho = Memory + Reasoning for AI agents, running 100% locally**

Traditional chat history stores what was said. Honcho reasons about what it means:

| Chat History | Honcho |
|--------------|--------|
| "User asked about PO 12345" | "User is stressed about PO approvals" |
| Stores exact messages | Detects behavioral patterns |
| Retrieves matches | Infers implicit preferences |

**Core Principle**: The Peer Paradigm - both users AND agents are "peers". This symmetric treatment enables multi-agent sessions, flexible identity management, and uniform observation patterns.

## When to Use

```dot
digraph local_honcho_decision {
    "Building AI agent?" [shape=diamond];
    "Need user memory?" [shape=diamond];
    "Simple history enough?" [shape=diamond];
    "Use LocalHoncho" [shape=box];
    "Use chat_history.json" [shape=box];

    "Building AI agent?" -> "Need user memory?" [label="yes"];
    "Building AI agent?" -> "Use chat_history.json" [label="no"];
    "Need user memory?" -> "Simple history enough?" [label="yes"];
    "Need user memory?" -> "Use LocalHoncho" [label="no - need patterns/reasoning"];
    "Simple history enough?" -> "Use chat_history.json" [label="yes"];
    "Simple history enough?" -> "Use LocalHoncho" [label="no - need personalization"];
}
```

**Use when:**
- Agent needs to remember user preferences across sessions
- You want to detect patterns in user behavior
- Personalization based on conversation history is required
- Multi-agent coordination with shared memory
- User asks "what does this user typically want?"

**Don't use when:**
- Simple message replay is sufficient
- Single-session only (no cross-session memory needed)
- No reasoning about user behavior required
- Existing RAG system already handles patterns

## Core Concepts

### The Four Primitives

| Primitive | Purpose | Example |
|-----------|---------|---------|
| **Workspace** | Isolate different applications | "sap-hr-bot", "sap-po-bot" |
| **Peer** | Any entity that changes over time | users, agents, groups, ideas |
| **Session** | Interaction thread between peers | A conversation, support ticket |
| **Message** | Data that triggers reasoning | Chat, events, documents |

### Why Peers Not Users?

```
Traditional: User ≠ Agent
Honcho: User IS Peer, Agent IS Peer

Benefits:
✓ Multi-participant sessions work naturally
✓ Agents can model other agents
✓ Symmetric observation and identity management
✓ "Who said what" applies to everyone
```

## Quick Reference

```python
# Import from the honcho-local plugin lib directory
import sys
sys.path.insert(0, "<plugin-install-path>/plugins/honcho-local/scripts")
from local_honcho import get_local_honcho

# Initialize (with thinking mode enabled)
memory = get_local_honcho(
    workspace_id="my-agent",
    model="qwen3.5:9b",
    think=True,
)

# Create peers
user = memory.peer("user-123", name="Alice")
agent = memory.peer("bot", peer_type="agent")

# Create session and add messages
session = memory.session("conv-1")
session.add_messages([
    {"role": "user", "content": "I need PO approval help", "metadata": {"peer_id": user.id}},
    {"role": "assistant", "content": "I can help with PO approval", "metadata": {"peer_id": agent.id}},
])

# Get context with summary (and thinking)
context = session.get_context(summary=True, include_thinking=True)
# → {"thinking": "...", "content": "Summary: ..."}

# Ask about user behavior (with thinking)
result = memory.chat(user.id, "What does this user need help with?", include_thinking=True)
# → {"thinking": "User mentioned PO...", "content": "The user needs help with..."}

# Get user profile (with thinking)
profile = memory.get_representation(user.id, include_thinking=True)
# → {"interests": [...], "thinking": "...", ...}

# Semantic search (uses embeddings)
results = memory.search(user.id, "PO approval", limit=5)
# → [{"content": "...", "score": 0.95}, ...]
```

## Implementation

### Requirements

- Ollama running locally (`ollama serve`)
- Python 3.10+
- `pip install ollama psycopg2-binary` (for Postgres support)

### Installation

```bash
# Ollama (for local LLM)
pip install ollama

# Start Ollama
ollama serve

# Pull models
ollama pull qwen3.5:9b          # Chat model with thinking support
ollama pull qwen3-embedding:0.6b  # For semantic search
```

### Basic Setup (Standalone)

```python
# From local_honcho.py in this skill directory
# Import from plugin lib
import sys
sys.path.insert(0, "<plugin-install-path>/plugins/honcho-local/scripts")
from local_honcho import get_local_honcho

# With JSON storage (default) + thinking mode
memory = get_local_honcho(
    workspace_id="my-workspace",
    ollama_base_url="http://localhost:11434",
    model="qwen3.5:9b",           # Chat model
    embedding_model="qwen3-embedding:0.6b",  # For search
    think=True,                   # Enable thinking mode
)

# With Postgres (optional, for better vector search)
memory = LocalHonchoMemory(
    workspace_id="my-workspace",
    use_postgres=True,
    postgres_uri="postgresql+psycopg://user:pass@localhost/db",
)
```

### Thinking Mode

Enable thinking mode to see the model's reasoning process:

```python
# Enable thinking mode
memory = get_local_honcho(
    workspace_id="my-workspace",
    think=True,  # or "low", "medium", "high" for GPT-OSS
)

# Get response with thinking
result = memory.chat(user.id, "What patterns do you see?", include_thinking=True)
# Returns: {"thinking": "<reasoning trace>", "content": "<answer>"}

# Get representation with thinking
profile = memory.get_representation(user.id, include_thinking=True)
# Returns: {"interests": [...], "thinking": "<reasoning>", ...}

# Context summary with thinking
context = session.get_context(summary=True, include_thinking=True)
# Returns: {"thinking": "<reasoning>", "content": "<summary + messages>"}
```

**Models that support thinking:**
- `qwen3.5:9b` - Recommended, fast with thinking
- `qwen3:8b` - Smaller alternative
- `deepseek-r1` - DeepSeek's reasoning model
- `gpt-oss` - With `think="low"|"medium"|"high"`

### Session Management

```python
# Create session
session = memory.session("ticket-12345", metadata={"urgent": True})

# Add messages (batch up to 100)
session.add_messages([
    {"role": "user", "content": "PO 4500012345 is stuck", "metadata": {"peer_id": user.id}},
    {"role": "assistant", "content": "Checking status...", "metadata": {"peer_id": agent.id}},
])

# Get context (last N messages, with optional summary)
context = session.get_context(summary=True, tokens=5000)
```

### Querying User Behavior

```python
# Natural language query
response = memory.chat(user_id, "What is this user's main concern?")
# Returns analyzed response based on all conversations

# Search for similar messages
results = memory.search(user_id, "PO approval", limit=5)

# Get user profile/representation
profile = memory.get_representation(user_id)
# Returns: interests, communication_style, frequent_topics, sentiment
```

### Async Interface

```python
# For use with PyTestSim framework
import sys
sys.path.insert(0, "path/to/PyTestSim")
from src.base.local_honcho_memory import get_async_memory

async def with_agent():
    memory = get_async_memory(workspace_id="my-agent")

    # Add message
    await memory.add_message("user", "Check PO status")

    # Get context
    context = await memory.get_context(summary=True)

    # Query user
    insights = await memory.chat_about_user("What does this user want?")
```

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Using dict/list for memory | No persistence, no reasoning, no cross-session | Use LocalHonchoMemory |
| Creating user_id and agent_id separately | Breaks peer paradigm, limits multi-agent | Treat both as peers |
| One session per user | Can't handle multiple conversations | Session per conversation thread |
| Not using summaries | Context window fills up | Enable `summary=True` |
| Skipping workspace_id | Data pollution between apps | Always namespace with workspace |

| Excuse | Reality |
|--------|---------|
| "Dict is faster" | 2ms vs 50ms - user won't notice, but they'll notice missing features |
| "We already have chat_history.json" | No reasoning, no pattern detection, no personalization |
| "Just use Redis" | No LLM-based reasoning about user behavior |
| "Too complex" | 3 lines to initialize, adds huge value |
| "I'll add later" | Refactoring memory architecture is painful, do it right first |

## Red Flags - STOP and Reconsider

- Using `dict` or `list` for user memory
- Storing messages without peer metadata
- No workspace isolation between apps
- Can't answer "what does this user typically want?"

## Integration with SAP AI Copilot

```python
# Option 1: Standalone (from honcho-local plugin)
import sys
sys.path.insert(0, "<plugin-install-path>/plugins/honcho-local/scripts")
from local_honcho import get_local_honcho

class SAPPOMemory:
    def __init__(self):
        self.memory = get_local_honcho(workspace_id="sap-po-agent")

# Option 2: From PyTestSim framework
import sys
sys.path.insert(0, "path/to/PyTestSim")
from src.base.local_honcho_memory import get_memory_provider

class SAPPOMemory:
    def __init__(self):
        self.memory = get_memory_provider(workspace_id="sap-po-agent")

    def remember_interaction(self, user_id: str, message: str, response: str):
        user = self.memory.peer(user_id)
        agent = self.memory.peer("sap-po-agent")
        session = self.memory.session(f"po-{user_id}")

        session.add_messages([
            {"role": "user", "content": message, "metadata": {"peer_id": user.id}},
            {"role": "assistant", "content": response, "metadata": {"peer_id": agent.id}},
        ])

    def get_user_context(self, user_id: str) -> str:
        """Get personalized context for next response"""
        context = self.memory.chat(user_id, "What context should I know about this user?")
        return context

    def user_needs_urgent_help(self, user_id: str) -> bool:
        """Detect if user typically needs urgent help"""
        profile = self.memory.get_representation(user_id)
        return profile.get("sentiment") == "urgent"
```

## Architecture Notes

- **Storage**: JSON by default, Postgres optional for vector search
- **LLM**: Ollama with qwen3:8b (replace with any model)
- **Reasoning**: Happens on `chat()` and `get_representation()` calls
- **Persistence**: Automatic on every `add_message()`

## Testing

```bash
# Run test suite
cd PyTestSim
python test_local_honcho.py

# Expected: 7/7 tests pass
```

## Real-World Impact

**Before (simple dict):**
```python
user_history["user-123"] = ["PO approval", "Leave balance"]
# Can't answer: What patterns? What's urgent? What style?
```

**After (LocalHoncho):**
```python
memory.chat(user_id, "What's urgent?")
# → "User has 3 urgent PO approvals pending, vendor waiting since yesterday"
memory.get_representation(user_id)
# → {"communication_style": "direct, prefers brief answers",
#    "interests": ["PO approval", "vendor management"],
#    "sentiment": "stressed-urgent"}
```
