# AgentBrain Installation Skill

Installs and configures AgentBrain memory system for Claude Code.

## Usage

The user wants to install AgentBrain when they say:
- "Install AgentBrain"
- "Set up memory"
- "I want you to remember things"
- "Enable persistent memory"

## Installation Steps

This skill automates the entire setup process:

1. Check prerequisites (Docker, Python)
2. Start Qdrant vector database
3. Verify Ollama embedding model
4. Test connection
5. Enable SessionStart hook

## Commands

After installation, the user can use:
- `/remember <info>` - Store information to memory
- `/recall <query>` - Retrieve relevant memories
- `/forget <topic>` - Delete a memory
- `/promote <memory> --to <scope>` - Share with team
