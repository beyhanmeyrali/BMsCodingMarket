# AgentBrain Setup Guide

Complete installation and configuration guide for AgentBrain.

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

## Requirements

### Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker Desktop | Latest | Run Qdrant vector database |
| Python | 3.10+ | Run AgentBrain scripts |
| Ollama | Latest | Local embedding generation |
| Claude Code | Latest | AI assistant with plugin support |

### Hardware

- **RAM**: 4GB+ recommended (8GB for multiple models)
- **Disk**: 10GB+ for Docker volumes and models
- **OS**: Windows 10/11, macOS, or Linux

## Quick Start

### 5-Minute Setup

```bash
# 1. Clone repository (if not already done)
cd /path/to/BMsCodingMarket

# 2. Start Qdrant
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml up -d

# 3. Pull embedding model
ollama pull qwen3-embedding:0.6b

# 4. Install plugin
/plugin marketplace add beyhanmeyrali/BMsCodingMarket
/plugin install agentbrain@bms-marketplace

# 5. Test
/remember "AgentBrain is now installed"
/recall "AgentBrain"
```

## Detailed Installation

### Step 1: Docker Setup

#### Windows

1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install with WSL 2 backend enabled
3. Start Docker Desktop
4. Verify: `docker --version`

#### Linux

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS

1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Install and start
3. Verify: `docker --version`

### Step 2: Start Qdrant

```bash
# Navigate to repository
cd /path/to/BMsCodingMarket

# Start Qdrant container
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml up -d

# Verify it's running
curl http://localhost:6333/collections

# Expected output:
# {"result":{"collections":[]},"status":"ok","time":0.0001}
```

#### Qdrant Web UI (Optional)

Access at: http://localhost:6333/dashboard

### Step 3: Install Ollama

#### Windows

```powershell
# Download installer
# https://ollama.ai/download/windows

# Or use winget
winget install Ollama.Ollama
```

#### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### macOS

```bash
# Download installer
# https://ollama.ai/download/mac
```

### Step 4: Pull Embedding Model

```bash
# Pull the model
ollama pull qwen3-embedding:0.6b

# Verify
ollama list

# Expected output includes:
# qwen3-embedding:0.6b
```

### Step 5: Install AgentBrain

#### Via Claude Code CLI

```bash
# Add marketplace
/plugin marketplace add beyhanmeyhali/BMsCodingMarket

# Install AgentBrain
/plugin install agentbrain@bms-marketplace

# Verify installation
/plugin list | grep agentbrain
```

#### Via Claude Code Desktop

1. Open Claude Code
2. Click **Plugins** → **Marketplace**
3. Add: `beyhanmeyrali/BMsCodingMarket`
4. Install: `agentbrain`

### Step 6: Configure Environment (Optional)

Create `.env` file in repository root:

```bash
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024

# Multi-tenant (for teams)
AGENTBRAIN_TEAM_ID=platform
AGENTBRAIN_ORG_ID=mycompany

# Auto-promotion
AUTO_PROMOTE_THRESHOLD=3

# Auto-capture
AGENTBRAIN_AUTO_CAPTURE=true

# Decay settings
DECAY_STALE_DAYS=60
DECAY_ROT_DAYS=90
```

## Configuration

### Repository-Level Configuration

Create `.agentbrain/config.yml` in your repository:

```yaml
# Team identification
team_id: platform
org_id: mycompany

# Memory settings
default_scope: team:platform
review_required: false

# Auto-promotion
auto_promote:
  enabled: true
  threshold: 5

# Reviewers
codeowners:
  - alice
  - bob
  - carol
```

### Team Memory Directory

Create `.agentbrain/memory/` for repo-based memories:

```
my-project/
├── .agentbrain/
│   ├── config.yml
│   └── memory/
│       ├── team/
│       │   └── conventions.md
│       └── project/
│           └── decisions.md
```

Example `conventions.md`:

```markdown
---
type: reference
scope: team:platform
---

# Team Conventions

## Development
- All projects use TypeScript
- GitHub Actions for CI/CD
- Conventional commits required

## Testing
- Minimum 80% coverage
- Integration tests for API changes
```

## Natural Language Triggers

AgentBrain captures information automatically through natural language — no commands needed.

### Explicit Storage Triggers

These phrases trigger immediate storage via the UserPromptSubmit hook:

| Phrase | Example |
|--------|---------|
| "Add to AgentBrain" | "Add to AgentBrain: we use Redis for caching" |
| "Add that to AgentBrain" | "That pattern works well. Add that to AgentBrain." |
| "Remember that" | "Remember that we always use TypeScript strict mode" |
| "Don't forget" | "Don't forget we use PostgreSQL not MongoDB" |
| "Keep in mind" | "Keep in mind: API routes use kebab-case" |
| "Note that" | "Note that we prefer tabs over spaces" |
| "Save to AgentBrain" | "Save to AgentBrain: team uses GitHub Actions" |

### Example Usage

```
You: "We decided to use Redis for session caching. Add that to AgentBrain."

[AgentBrain] Stored to memory

Later, when you or a teammate asks about caching:
→ AgentBrain automatically injects the relevant context
```

### Auto-Capture (SessionEnd)

Additionally, AgentBrain automatically captures insights at session end:

- "We decided to use X"
- "The team uses Y"
- "I prefer Z"

No manual action required.

## Verification

### Test 1: Natural Language Storage

```bash
# Try the natural language trigger
"Add to AgentBrain: AgentBrain is now installed"
```

Expected output:
```
[AgentBrain] Stored to memory
```

### Test 2: Manual Command Storage

```bash
/remember "Testing AgentBrain installation"
```

Expected output:
```
# Memory Stored

**File:** `user_testing_agentbrain_installation_20260415.md`
**Type:** user
**Scope:** user:{username}
**ID:** abc123...
```

### Test 2: Memory Retrieval

```bash
/recall "AgentBrain"
```

Expected output:
```
# Relevant Memories (1 found)

## 1. user_testing_agentbrain_installation_20260415.md
**Scope:** user:{username}
**Type:** user

Testing AgentBrain installation
```

### Test 3: Multi-Tenant Isolation

```bash
# Run test suite
cd plugins/agentbrain
python tests/test_multi_tenant.py
```

Expected:
```
12/12 tests passed
SUCCESS: All tests passed!
```

### Test 4: Health Dashboard

```bash
python scripts/governance/memory_stats.py
```

Expected: Memory counts and health scores displayed

## Troubleshooting

### Qdrant Issues

**Problem**: Connection refused

```bash
# Solution: Check Qdrant is running
docker ps | grep qdrant

# Restart if needed
docker compose -f plugins/agentbrain/docker/qdrant-compose.yml restart
```

**Problem**: Wrong collection name

```bash
# Solution: Check collection exists
curl http://localhost:6333/collections/agentbrain_memories

# Create if missing (automatic, but can force)
# via Python: qdrant.initialize()
```

### Ollama Issues

**Problem**: Model not found

```bash
# Solution: Pull model again
ollama pull qwen3-embedding:0.6b

# Verify
ollama list
```

**Problem**: Wrong dimension

```bash
# Solution: Check model dimension
ollama show qwen3-embedding:0.6b

# Set in .env
EMBEDDING_DIMENSION=1024
```

### Memory Issues

**Problem**: Memories not storing

```bash
# Check 1: Verify Qdrant connection
curl http://localhost:6333/

# Check 2: Verify Ollama
ollama list

# Check 3: Check file permissions
ls -la ~/.claude/memory/
```

**Problem**: No results from /recall

```bash
# Check 1: Verify memories exist
curl http://localhost:6333/collections/agentbrain_memories/points

# Check 2: Verify scopes
python scripts/query.py --scopes

# Check 3: Lower threshold
/recall "test" --min-score 0.3
```

### Windows-Specific Issues

**Problem**: Colons in filenames

Files with colons (`:`) are invalid on Windows. AgentBrain sanitizes automatically.

**Problem**: Path too long

Windows has a 260 character path limit. Use shorter repository names or enable long paths:

```powershell
# Enable long paths (Windows 10+)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Docker Issues

**Problem**: Port 6333 already in use

```bash
# Solution 1: Stop conflicting service
net stop <service_name>

# Solution 2: Change Qdrant port
# Edit docker/qdrant-compose.yml:
# ports:
#   - "6334:6333"  # Use 6334 instead

# Update .env:
# QDRANT_PORT=6334
```

**Problem**: Out of memory

```bash
# Solution: Limit Docker memory
# Docker Desktop → Settings → Resources → Memory
# Set to 4GB or more
```

## Advanced Setup

### Custom Embedding Model

Use a different Ollama model:

```bash
# Pull alternative model
ollama pull nomic-embed-text

# Configure .env
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
```

### Remote Qdrant

Connect to remote Qdrant instance:

```bash
# .env configuration
QDRANT_HOST=qdrant.example.com
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key
```

### Multi-Repository Setup

Share team memories across repositories:

```yaml
# .agentbrain/config.yml
team_id: platform  # Same across all repos
org_id: acme       # Same across all org
```

### Scheduled Decay Sweep

Set up automatic cleanup:

```bash
# Linux cron
0 2 * * * cd /path/to/agentbrain && \
  python scripts/governance/decay_sweep.py --delete

# Windows Task Scheduler
# Schedule task to run daily at 2 AM
# Program: python
# Arguments: scripts\governance\decay_sweep.py --delete
```

### Backup and Restore

**Backup Qdrant:**

```bash
# Export collection
curl http://localhost:6333/collections/agentbrain_memories \
  -o qdrant_backup.json

# Backup memory files
tar -czf memories_backup.tar.gz ~/.claude/memory/
```

**Restore:**

```bash
# Import collection
curl -X PUT http://localhost:6333/collections/agentbrain_memories \
  -H 'Content-Type: application/json' \
  -d @qdrant_backup.json

# Restore memory files
tar -xzf memories_backup.tar.gz -C ~/
```

## Next Steps

After installation:

1. [Configure team scoping](#configuration)
2. [Import existing knowledge](../README.md#extractors)
3. [Set up repo-based memories](#repository-level-configuration)
4. [Configure scheduled maintenance](#scheduled-decay-sweep)

## Support

- **Issues**: https://github.com/beyhanmeyrali/BMsCodingMarket/issues
- **Documentation**: [README](../README.md)
- **Claude Guide**: [CLAUDE_GUIDE.md](../../plugins/agentbrain/CLAUDE_GUIDE.md)

## License

MIT

---

**Author:** [Beyhan Meyrali](https://github.com/beyhanmeyrali)
