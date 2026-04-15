# AgentBrain Scenario Analysis

Testing if current capabilities fit real user scenarios.

## User Scenarios

### Scenario 1: "Remember this for me"
**User**: "Remember that I always use TypeScript strict mode"

**What Claude should do**:
- Invoke `/remember "I always use TypeScript strict mode"`
- Confirm memory was stored

**Current capability**: ✅ `/remember` skill exists

**Gap**: Claude doesn't know WHEN to use it (needs trigger pattern)


### Scenario 2: "What did I say about X?"
**User**: "What did I tell you about testing?"

**What Claude should do**:
- Invoke `/recall "testing"`
- Present relevant memories

**Current capability**: ✅ `/recall` skill exists

**Gap**: Claude doesn't know this skill exists for answering such questions


### Scenario 3: New session context
**User**: Opens new session and continues working

**What Claude should do**:
- SessionStart hook automatically queries relevant memories
- Inject them into context

**Current capability**: ✅ SessionStart hook exists

**Gap**: Not proven to work; needs testing


### Scenario 4: "Forget that"
**User**: "Actually, forget what I said about TypeScript"

**What Claude should do**:
- Invoke `/forget "TypeScript"`

**Current capability**: ✅ `/forget` skill exists

**Gap**: Fuzzy matching needs improvement


### Scenario 5: Team knowledge sharing
**User**: "This pattern we used on the payment module would be useful for the whole team"

**What Claude should do**:
- Recognize this is promotion-worthy
- Invoke `/promote <memory> --to team:platform`

**Current capability**: ✅ `/promote` skill exists

**Gap**: Claude doesn't know how to find the memory to promote


### Scenario 6: First-time user
**User**: "I want you to remember things between sessions"

**What Claude should do**:
- Know to install AgentBrain
- Guide through setup automatically

**Current capability**: ❌ No installation skill

**Gap**: Manual setup required


## Critical Gaps

1. **Skill Discovery** - Claude doesn't know AgentBrain skills exist
2. **Trigger Patterns** - Claude doesn't know WHEN to use each skill
3. **Installation** - No auto-setup for Docker/Qdrant/Ollama
4. **Session Integration** - Hook not proven to work

## Required: Claude Code User Guide

The user guide must be:
- Written FOR Claude Code (not humans)
- In SKILL.md format (Claude can read it)
- Describe WHEN to use each capability
- Include examples of trigger phrases

Example:
```markdown
# AgentBrain User Guide for Claude Code

## When to Use

### Remembering Information
Use the /remember skill when the user says:
- "Remember that..."
- "Don't forget..."
- "Keep in mind..."
- "Note that..."

### Recalling Information
Use the /recall skill when the user asks:
- "What did I say about...?"
- "What do you know about...?"
- "Have I told you about...?"
- "Remind me about..."
```
