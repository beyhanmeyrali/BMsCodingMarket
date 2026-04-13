# Honcho Local Setup for SAP AI Copilot

## What is Honcho?

Honcho is a **memory library for building stateful agents** that goes beyond simple RAG by using formal logic reasoning to extract latent information from conversations.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Workspaces** | Top-level containers for different applications/environments |
| **Peers** | Any entity that persists but changes (users, agents, groups) |
| **Sessions** | Interaction threads between peers |
| **Messages** | Data units that trigger background reasoning |

### Benefits for SAP AI Copilot

- **User preference tracking** across sessions
- **Behavior pattern analysis** via reasoning
- **Context-aware responses** with history
- **Multi-agent coordination** support

---

## Setup Instructions

### 1. Start Docker Desktop

First, make sure Docker Desktop is running on Windows.

```powershell
# Start Docker Desktop from Windows Start Menu
# Or run: start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### 2. Start Postgres with pgvector

```bash
cd honcho-local
docker compose up -d
```

This will start Postgres on port **5433** (not default 5432 to avoid conflicts).

### 3. Configure API Keys

Edit the `.env` file and add at least ONE of these:

```bash
# Edit this file with your actual API keys
notepad .env
```

Required keys (at least one):
- `LLM_ANTHROPIC_API_KEY` - For Claude models (recommended for reasoning)
- `LLM_OPENAI_API_KEY` - For GPT models (for embeddings)
- `LLM_GEMINI_API_KEY` - For Google Gemini (cost-effective reasoning)

### 4. Install Additional Dependencies

```bash
pip install psycopg2-binary sqlalchemy alembic
```

### 5. Run Migrations

Once Docker is running and API keys are configured:

```bash
cd honcho-local
python run_migrations.py
```

---

## Quick Test

Test your setup with the Python SDK:

```python
from honcho import Honcho
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Honcho
honcho = Honcho(workspace_id="sap-ai-copilot-test")

# Create peers
user = honcho.peer("test-user")
agent = honcho.peer("sap-agent")

# Create a session
session = honcho.session("test-session-1")

# Add messages
session.add_messages([
    user.message("Hello, I need help with a PO approval"),
    agent.message("I can help with that. Which PO needs approval?")
])

# Get context
context = session.context(summary=True)
print(f"Context: {context}")

# Chat with the peer
response = user.chat("What is the user working on?")
print(f"Response: {response}")
```

---

## Integration with PyTestSim

To integrate Honcho with your existing PyTestSim testing framework:

1. Add `honcho-ai` to `PyTestSim/requirements.txt`
2. Create a new memory provider at `PyTestSim/src/base/honcho_memory.py`
3. Hook into the existing `chat_history.json` storage

---

## Docker Commands

```bash
# Start database
docker compose up -d

# Stop database
docker compose down

# View logs
docker compose logs -f database

# Connect to database
docker exec -it honcho-postgres psql -U honcho -d honcho_dev
```

---

## Troubleshooting

### Docker won't start
- Make sure Docker Desktop is running
- Check WSL2 is enabled: `wsl --list --verbose`

### Connection errors
- Check Postgres is running: `docker compose ps`
- Verify port 5433 is not in use: `netstat -ano | findstr 5433`

### API Key errors
- Verify your key is set in `.env`
- Try testing with a simple API call first

---

## Next Steps

1. Start Docker Desktop
2. Add your API key to `.env`
3. Run `docker compose up -d`
4. Run migrations
5. Test with Python script

---

## Resources

- [Honcho Documentation](https://docs.honcho.dev/v3)
- [GitHub Repository](https://github.com/plastic-labs/honcho)
- [Python SDK Reference](https://docs.honcho.dev/v3/documentation/sdk/python)
