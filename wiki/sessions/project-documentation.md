---
session_id: project-documentation
title: Conversation - project-documentation
created_at: 2026-04-13T11:19:14.307193
workspace: bms-marketplace
message_count: 2
participants: ['bms-marketplace', 'user']
---

# Conversation - project-documentation

## Summary

Conversation log from honcho memory.

## Participants

- **BMsCodingMarket** (agent) - [[bms-marketplace]]
- **User** (user) - [[user]]

## Transcript

### 2026-04-13 11:19\n
**User** (user):\n
The BMsCodingMarket project is a Claude Code marketplace plugin called honcho-local.

Purpose:
- Local-first memory and reasoning for AI agents
- Uses Ollama instead of cloud APIs (no API keys needed)
- Based on Honcho concepts but runs 100% locally

Core Features:
1. Peer Paradigm - users and agents are both "peers"
2. Session Management - isolated conversation threads
3. Natural Language Queries - ask "What does this user want?"
4. Thinking Mode - see model's reasoning trace
5. Semantic Search - vector embeddings for finding similar messages

Project Structure:
- .claude-plugin/marketplace.json - Marketplace manifest
- commands/install.md - /honcho-install command
- commands/check.md - /honcho-check command
- scripts/local_honcho.py - Core library implementation
- scripts/setup.py - Installation script
- scripts/check.py - Verification script
- skills/honcho-local/SKILL.md - Auto-discovered skill documentation
- hooks/hooks.json - Session start hooks

Tech Stack:
- Python 3.10+
- Ollama (local LLM runner)
- qwen3.5:9b (chat model with thinking)
- qwen3-embedding:0.6b (semantic search)

Key Classes:
- LocalHoncho: Main memory provider
- Session: Conversation thread manager
- Peer: User/agent representation
- Message: Individual data unit

Main Methods:
- get_local_honcho() - Factory function
- memory.peer(id, name, type) - Create/get peer
- memory.session(id) - Create/get session
- session.add_messages(msgs) - Add messages
- memory.chat(peer_id, question) - Ask about peer
- memory.get_representation(peer_id) - Get peer profile
- memory.search(peer_id, query) - Semantic search
\n
### 2026-04-13 11:19\n
**BMsCodingMarket** (assistant):\n
I've documented the BMsCodingMarket project. This is a honcho-local plugin that provides:

1. **Local-first memory** - No cloud APIs needed
2. **Thinking mode** - See model reasoning (qwen3.5:9b)
3. **Semantic search** - Vector embeddings (qwen3-embedding:0.6b)
4. **Easy install** - /honcho-install command
5. **Verification** - /honcho-check command

The plugin follows Claude Code marketplace structure with commands, skills, hooks, and scripts directories.
\n

## Topics\n\n- Agents\n- Bmscodingmarket\n- Called\n- Claude\n- Command\n- Concepts\n- Conversation\n- Documentation\n- Documented\n- Embeddings\n