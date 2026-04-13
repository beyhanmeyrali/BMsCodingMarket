---
name: honcho-check
description: Verify honcho-local plugin installation and Ollama connectivity
---

# Honcho Local Check

This command verifies that the honcho-local plugin is properly configured and Ollama is working.

## What gets checked

1. **Ollama installation** - Is Ollama installed and accessible?
2. **Ollama service** - Is Ollama running on port 11434?
3. **Models** - Are qwen3.5:9b and qwen3-embedding:0.6b available?
4. **Python dependencies** - Are ollama and psycopg2-binary installed?
5. **Plugin paths** - Can the local_honcho module be imported?
6. **Basic functionality** - Can we create a simple memory and add a message?

## Usage

Run this command to check everything:
```
/honcho-check
```

## Expected output

```
[Honcho Local Installation Check]

[1/6] Checking Ollama installation...
[OK] Ollama is installed

[2/6] Checking Ollama service...
[OK] Ollama is running on http://localhost:11434

[3/6] Checking models...
[OK] qwen3.5:9b is available
[OK] qwen3-embedding:0.6b is available

[4/6] Checking Python dependencies...
[OK] ollama is installed
[OK] psycopg2-binary is installed

[5/6] Checking plugin paths...
[OK] local_honcho module can be imported

[6/6] Testing basic functionality...
[OK] Can create memory and add messages

[SUCCESS] Honcho Local is ready to use!
```

## Troubleshooting

**Ollama not running**: Start Ollama with `ollama serve`
**Model missing**: Run `/honcho-install` to download models
**Import error**: Check Python path and reinstall dependencies
**Connection refused**: Make sure Ollama is running on port 11434
