---
name: forget
description: Remove a stored memory from AgentBrain
---

Remove a memory from AgentBrain. Deletes from both the vector database and file storage.

## Usage

```
/forget <memory-name>
```

## Examples

- `/forget user_preferences.md` - Delete a specific memory
- `/forget api_decisions` - Delete by name (with or without .md)

## Warning

This operation is immediate and permanent. Once forgotten, memories cannot be recovered unless you have a backup.

Tip: Use `/recall` first to find the exact memory name before forgetting.
