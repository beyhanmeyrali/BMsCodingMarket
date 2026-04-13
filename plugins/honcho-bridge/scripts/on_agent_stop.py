#!/usr/bin/env python3
"""
Claude Code Stop hook — reads the session transcript from stdin JSON,
extracts the last assistant turn, and stores it to Honcho memory.

Claude Code passes JSON on stdin:
  {
    "session_id": "...",
    "transcript_path": "/path/to/transcript.jsonl",
    "hook_event_name": "Stop",
    ...
  }
"""

import sys
import json
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
STORE_SCRIPT = SCRIPTS_DIR / "store_to_honcho.py"


def extract_last_assistant_turn(transcript_path: str) -> str | None:
    path = Path(transcript_path)
    if not path.exists():
        return None

    last_assistant_text: list[str] = []
    last_human_text: str = ""

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = entry.get("role", "")

            if role == "human":
                parts = entry.get("content", [])
                if isinstance(parts, list):
                    for p in parts:
                        if isinstance(p, dict) and p.get("type") == "text":
                            last_human_text = p.get("text", "").strip()
                elif isinstance(parts, str):
                    last_human_text = parts.strip()

            elif role == "assistant":
                texts: list[str] = []
                parts = entry.get("content", [])
                if isinstance(parts, list):
                    for p in parts:
                        if isinstance(p, dict) and p.get("type") == "text":
                            t = p.get("text", "").strip()
                            if t:
                                texts.append(t)
                elif isinstance(parts, str) and parts.strip():
                    texts.append(parts.strip())
                if texts:
                    last_assistant_text = texts

    if not last_assistant_text:
        return None

    combined = "\n".join(last_assistant_text)
    summary = combined[:1500]

    if last_human_text:
        return f"User: {last_human_text[:300]}\nAgent: {summary}"
    return f"Agent: {summary}"


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id: str = data.get("session_id", "unknown")
    transcript_path: str = data.get("transcript_path", "")

    summary = extract_last_assistant_turn(transcript_path) if transcript_path else None

    if not summary:
        sys.exit(0)

    result = subprocess.run(
        [
            sys.executable,
            str(STORE_SCRIPT),
            "--session-id",
            session_id,
            "--summary",
            summary,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"[honcho-memory] store failed: {result.stderr}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
