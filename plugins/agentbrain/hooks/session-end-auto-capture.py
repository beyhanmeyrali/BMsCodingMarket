"""
AgentBrain SessionEnd Auto-Capture Hook

Automatically captures insights from conversations to prevent knowledge silos.
Runs at session end to extract and store valuable learnings.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Add plugin scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from skill_remember import skill_remember
from skill_promote import skill_promote, resolve_memory_name
from query import get_allowed_scopes


# Patterns that indicate valuable information to capture
CAPTURE_PATTERNS = {
    "decision": [
        r"we decided to",
        r"we're using",
        r"we chose",
        r"going with",
        r"selected",
        r"standardize on",
    ],
    "convention": [
        r"we always",
        r"we never",
        r"team uses",
        r"our convention",
        r"our standard",
        r"best practice",
    ],
    "preference": [
        r"i prefer",
        r"i like",
        r"i always",
        r"i never",
        r"my preference",
    ],
    "lesson": [
        r"learned",
        r"lesson",
        r"don't.*again",
        r"avoid",
        r"watch out for",
        r"be careful",
    ],
}


def extract_insights(conversation_text: str) -> list:
    """
    Extract potential insights from conversation.

    Args:
        conversation_text: Full conversation transcript

    Returns:
        List of (type, insight_text) tuples.
    """
    insights = []
    sentences = re.split(r'[.!?]+', conversation_text)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 500:
            continue

        sentence_lower = sentence.lower()

        for insight_type, patterns in CAPTURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    insights.append((insight_type, sentence))
                    break

    return insights


def should_promote_to_team(insight: str, insight_type: str) -> bool:
    """
    Determine if an insight should be promoted to team scope.

    Args:
        insight: The insight text
        insight_type: Type of insight (decision, convention, etc.)

    Returns:
        True if should promote to team.
    """
    # Conventions and decisions are team-relevant by default
    if insight_type in ["convention", "decision"]:
        # Unless it's clearly personal
        personal_indicators = ["i prefer", "i like", "my"]
        insight_lower = insight.lower()
        return not any(indicator in insight_lower for indicator in personal_indicators)

    return False


def auto_capture_and_store(conversation_text: str) -> dict:
    """
    Automatically capture and store insights from conversation.

    Args:
        conversation_text: The conversation transcript

    Returns:
        Results dict with counts and errors.
    """
    if not conversation_text or len(conversation_text) < 100:
        return {"skipped": "Conversation too short"}

    results = {
        "insights_found": 0,
        "stored": 0,
        "promoted": 0,
        "errors": [],
    }

    # Extract insights
    insights = extract_insights(conversation_text)
    results["insights_found"] = len(insights)

    # Get scopes for promotion
    scopes = get_allowed_scopes()
    team_scope = next((s for s in scopes if s.startswith("team:")), None)

    for insight_type, insight_text in insights:
        try:
            # Store the memory
            result = skill_remember(insight_text)

            if "Memory Stored" in result:
                results["stored"] += 1

                # Check if should promote to team
                if team_scope and should_promote_to_team(insight_text, insight_type):
                    # Extract memory name from result
                    # Result format: "**File:** `user_xxx_timestamp.md`"
                    import re
                    match = re.search(r"`([^`]+)\.md`", result)
                    if match:
                        memory_name = match.group(1)
                        promote_result = skill_promote(memory_name, team_scope)

                        if "Promoted" in promote_result:
                            results["promoted"] += 1

        except Exception as e:
            results["errors"].append(str(e))

    return results


def main():
    """
    SessionEnd hook entry point.

    Reads conversation from stdin, extracts insights,
    and stores valuable ones automatically.
    """
    # Skip if auto-capture is disabled
    if os.environ.get("AGENTBRAIN_AUTO_CAPTURE", "true").lower() == "false":
        return

    # Read conversation transcript
    # Claude Code provides this via stdin or environment variable
    conversation_text = sys.stdin.read()

    # Also check for transcript file
    if not conversation_text:
        transcript_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
        if transcript_path and Path(transcript_path).exists():
            try:
                conversation_text = Path(transcript_path).read_text(encoding="utf-8")
            except Exception:
                pass

    # Process conversation
    results = auto_capture_and_store(conversation_text)

    # Log results (non-blocking)
    if results.get("insights_found", 0) > 0:
        log_msg = f"[AgentBrain] Auto-captured {results['insights_found']} insights, "
        log_msg += f"stored {results['stored']}, promoted {results['promoted']}"
        print(log_msg, file=sys.stderr)


if __name__ == "__main__":
    main()
