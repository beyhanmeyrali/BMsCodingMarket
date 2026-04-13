---
name: honcho-status
description: Check Honcho system health, connection status, and workspace statistics.
---

# Honcho System Status

Check if your local Honcho memory system is working correctly.

## Usage

```
/honcho-status
```

## What It Shows

- **Connection**: API health and latency
- **Workspace**: Current workspace ID
- **Statistics**: Peer count, session count, message count
- **Warnings**: If messages exist but no observations (deriver not processed yet)

## Example Output

```
==================================================
HONCHO SYSTEM STATUS
==================================================

Connection: OK
Workspace: my-project

Statistics:
  Peers: 1
  Sessions: 3
  Messages: 15

[!] Deriver hasn't processed messages yet
    Wait ~1 minute or check: docker compose logs deriver
==================================================
```
