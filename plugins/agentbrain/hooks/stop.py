"""
AgentBrain Stop Hook

Spawns the memory-curator subagent at session end to analyze
the conversation and extract candidate memories.

The curator runs asynchronously and doesn't block session shutdown.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime


def get_transcript_path() -> str:
    """
    Get the path to the current session transcript.

    The transcript location varies by Claude Code implementation.
    This function checks multiple possible locations.

    Returns:
        Path to transcript file or empty string if not found.
    """
    # Check environment variables first
    transcript_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH", "")
    if transcript_path and Path(transcript_path).exists():
        return transcript_path

    # Check common transcript locations
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if session_id:
        # Common locations for transcripts
        possible_paths = [
            Path.home() / ".claude" / "sessions" / f"{session_id}.md",
            Path.home() / ".claude" / "transcripts" / f"{session_id}.md",
            Path(tempfile.gettempdir()) / "claude" / "sessions" / f"{session_id}.md",
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)

    return ""


def get_memory_index() -> str:
    """
    Get the current MEMORY.md index content.

    Returns:
        Content of MEMORY.md or empty string if not found.
    """
    memory_dir = Path(os.environ.get("MEMORY_DIR", "~/.claude/memory")).expanduser()
    index_file = memory_dir / "MEMORY.md"

    if index_file.exists():
        return index_file.read_text(encoding="utf-8")

    return ""


def should_run_curator() -> bool:
    """
    Determine if the curator should run for this session.

    Returns:
        True if curator should run, False otherwise.
    """
    # Check if curator is disabled
    if os.environ.get("AGENTBRAIN_CURATOR_AUTO_RUN", "true").lower() == "false":
        return False

    # Check if this is a subagent session (don't recurse)
    if os.environ.get("CLAUDE_SUBAGENT", "").lower() == "true":
        return False

    return True


def prepare_curator_prompt(transcript: str, memory_index: str) -> str:
    """
    Prepare the prompt for the memory-curator subagent.

    Args:
        transcript: Session transcript
        memory_index: Current MEMORY.md content

    Returns:
        Prompt for the subagent.
    """
    # Truncate transcript if too long (subagents have context limits)
    max_transcript_length = 50000  # ~50K chars
    if len(transcript) > max_transcript_length:
        # Keep the beginning and end, truncate the middle
        keep_start = max_transcript_length // 2
        keep_end = max_transcript_length // 2
        transcript = transcript[:keep_start] + "\n\n... [truncated] ...\n\n" + transcript[-keep_end:]

    return f"""# Session Transcript

{transcript}

# Current Memory Index

{memory_index if memory_index else "(No existing memories)"}

# Task

Extract and curate memories from this session. Follow the memory-curator subagent instructions:

- Identify user preferences, feedback patterns, project decisions, and references
- Classify each by type (user/feedback/project/reference) and scope
- Check for duplicates against existing memories
- Emit JSON as specified in the memory-curator.md instructions

Output ONLY the JSON. No other text.
"""


def spawn_curator_subagent() -> bool:
    """
    Spawn the memory-curator subagent.

    Returns:
        True if successfully spawned, False otherwise.
    """
    # Get transcript
    transcript_path = get_transcript_path()
    if not transcript_path:
        print("[AgentBrain] No transcript found, skipping curation", file=sys.stderr)
        return False

    try:
        transcript = Path(transcript_path).read_text(encoding="utf-8")
    except Exception as e:
        print(f"[AgentBrain] Failed to read transcript: {e}", file=sys.stderr)
        return False

    # Get memory index
    memory_index = get_memory_index()

    # Prepare prompt
    prompt = prepare_curator_prompt(transcript, memory_index)

    # Write to a temp file for the subagent
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
    curator_dir = plugin_root / ".agentbrain"
    curator_dir.mkdir(exist_ok=True)

    prompt_file = curator_dir / "curator_prompt.txt"
    output_file = curator_dir / "curator_output.json"

    prompt_file.write_text(prompt, encoding="utf-8")

    # Signal that curation is needed by writing a marker file
    # The SubagentStop hook will process the output
    marker_file = curator_dir / "curation_needed.txt"
    marker_file.write_text(
        f"started_at={datetime.now().isoformat()}\n"
        f"prompt_file={prompt_file}\n"
        f"output_file={output_file}\n"
    )

    print(f"[AgentBrain] Curator job prepared: {output_file}", file=sys.stderr)
    return True


def main():
    """Main entry point for Stop hook."""

    # Skip if disabled
    if not should_run_curator():
        return

    # Check if AgentBrain is enabled
    if os.environ.get("AGENTBRAIN_ENABLED", "true").lower() == "false":
        return

    # Spawn curator subagent
    spawn_curator_subagent()


if __name__ == "__main__":
    main()
