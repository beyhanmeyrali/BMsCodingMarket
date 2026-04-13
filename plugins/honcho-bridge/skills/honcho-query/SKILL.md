---
name: honcho-query
description: Query Honcho memory using peer.chat() to retrieve learned information about a user. Use when you need to recall preferences, context, or facts from previous conversations.
---

# Honcho Memory Query

Query what Honcho has learned about a user from previous conversations.

## Usage

```bash
python plugins/honcho-bridge/scripts/honcho_query.py \
  --base-url http://localhost:8000 \
  --workspace <workspace-id> \
  --peer <peer-id> \
  --query "<your question about the user>"
```

## Examples

```bash
# Ask about user preferences
python plugins/honcho-bridge/scripts/honcho_query.py \
  --workspace my-project --peer alice \
  --query "What are Alice's coding preferences?"

# Ask about past decisions
python plugins/honcho-bridge/scripts/honcho_query.py \
  --workspace my-project --peer alice \
  --query "What database decisions were made?"

# Ask about user's background
python plugins/honcho-bridge/scripts/honcho_query.py \
  --workspace my-project --peer alice \
  --query "Tell me about this user's background and role"
```

## How it works

1. Embeds your query using the embedding model (qwen3-embedding:0.6b)
2. Runs vector similarity search over all observations for the peer
3. Sends top-k matches to the LLM to synthesize a grounded answer
4. Returns the answer with citations

## When to use

- Before making technical decisions — check what was decided before
- When user returns after time away — recall their context
- To avoid repeating questions — check if Honcho already knows
- To understand user preferences — stack, editor, communication style
