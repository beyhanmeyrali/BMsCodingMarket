# AgentBrain User Guide for Claude Code

> This guide is written FOR Claude Code to understand when and how to use AgentBrain capabilities.

## Overview

AgentBrain gives you persistent memory across sessions. You can remember user preferences, project decisions, team conventions, and more.

## When to Use AgentBrain

### Remembering Information

Use `/remember` when the user indicates information should be stored:

**Trigger phrases:**
- "Add to AgentBrain..."
- "Add that to AgentBrain..."
- "Save to AgentBrain..."
- "Remember that..."
- "Don't forget..."
- "Keep in mind..."
- "Note that..."
- "For future reference..."

**IMPORTANT: "Add to AgentBrain" triggers immediate storage via UserPromptSubmit hook.**

**Examples:**
```
User: "Add to AgentBrain: we use Redis for session caching"
→ Automatic: Stored immediately (no /remember needed)

User: "Add those to AgentBrain"
→ Automatic: Extracts context from conversation and stores

User: "Remember that I always use TypeScript strict mode"
→ Automatic: Stored immediately

User: "Note that we use PostgreSQL not MongoDB"
→ Automatic: Stored immediately
```

### Recalling Information

Use `/recall` when the user asks about past information:

**Trigger phrases:**
- "What did I say about...?"
- "What do you know about...?"
- "Have I told you about...?"
- "Remind me about..."
- "How do I...?" (for process questions)
- "What are our conventions for...?"

**Examples:**
```
User: "What did I tell you about testing?"
→ You invoke: /recall "testing"

User: "How do I deploy to production?"
→ You invoke: /recall "deployment production"
```

### Forgetting Information

Use `/forget` when the user wants to remove a memory:

**Trigger phrases:**
- "Forget that..."
- "Don't remember..."
- "Remove that from memory"
- "I didn't mean that"

**Examples:**
```
User: "Forget what I said about TypeScript"
→ You invoke: /forget "TypeScript"
```

### Promoting to Team

Use `/promote` when the user indicates information should be shared:

**Trigger phrases:**
- "This would be good for the team to know"
- "Share this with the team"
- "Make this a team convention"
- "Everyone should know this"

**Examples:**
```
User: "This pattern would be useful for the whole team"
→ You invoke: /promote <recent_memory> --to team:platform
```

## Scope Awareness

Memories exist at different scopes. Understand that:

- **user:XXX** - Only this user sees these memories
- **team:XXX** - All team members can see these
- **project:XXX** - Anyone working on this project can see these
- **org:XXX** - Everyone in the organization can see these

When a user shares something team-wide, suggest promotion.

## Session Start Behavior

When a new session starts, AgentBrain automatically:
1. Syncs repo-based team memories
2. Queries for relevant context
3. Injects memories into your context

You don't need to do anything - memories appear automatically if relevant.

## Memory Quality Guidelines

What IS worth remembering:
- User preferences and workflows
- Project-specific decisions
- Team conventions and patterns
- Architecture decisions
- Lessons learned from incidents

What is NOT worth remembering:
- Temporary debugging commands
- One-time actions
- Transient state
- Obvious information

## Error Handling

If `/recall` returns no results:
- The information may not have been stored
- Try rephrasing the query
- Ask the user to clarify what they're looking for

If `/remember` fails:
- Check Qdrant is running
- Check Ollama is available
- Report the error to the user

## Integration Examples

### Example 1: Learning User Preferences
```
User: "I prefer tabs over spaces in my code"

You should:
1. Invoke: /remember "User prefers tabs over spaces in code"
2. Confirm: "Got it. I'll remember you prefer tabs."
```

### Example 2: Answering from Memory
```
User: "What's our API for user authentication?"

You should:
1. Invoke: /recall "authentication API"
2. If found: Present the memory
3. If not found: "I don't have that information. Would you like me to remember it?"
```

### Example 3: Team Knowledge Sharing
```
User: "We decided to use Redis for caching. This is good practice."

You should:
1. Invoke: /remember "Team decided to use Redis for caching"
2. Suggest: "This seems like a useful team convention. Would you like me to promote it to team:platform?"
```

## Commands Summary

| Command | When to Use | Purpose |
|---------|-------------|---------|
| `/remember <text>` | User wants to store info | Create memory |
| `/recall <query>` | User asks about past info | Retrieve memories |
| `/forget <topic>` | User wants to remove | Delete memory |
| `/promote <mem> --to <scope>` | Info should be shared | Widen scope |

## Testing Your Understanding

After reading this guide, you should be able to:

1. Recognize when the user wants you to remember something
2. Know which command to use for each request type
3. Understand memory scopes and when to suggest promotion
4. Handle cases where memory retrieval returns no results
5. Proactively suggest promoting useful information to the team
