#!/usr/bin/env python3
"""
Memory-driven suggestions for Honcho.

Proactively suggests relevant observations based on:
- Current context (file, branch)
- Semantic similarity
- Pattern detection for conflicts
"""

import os
import sys
import argparse
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Fix Windows encoding issue
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from honcho import Honcho as HonchoClient
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False

# Add hooks directory for auto_tagger
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
try:
    import auto_tagger
    TAGGER_AVAILABLE = True
except ImportError:
    TAGGER_AVAILABLE = False


def load_env_config():
    """Load configuration from .env file in current directory."""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env_config()


class MemorySuggester:
    """Proactive memory suggestion engine."""

    def __init__(self, base_url: str, workspace: str, peer_id: str):
        """Initialize the suggester."""
        if not HONCHO_AVAILABLE:
            raise ImportError("honcho-ai not installed")

        self.client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )
        self.peer = self.client.peer(peer_id)
        self.workspace = workspace
        self.peer_id = peer_id

    def suggest_for_context(
        self,
        query: str,
        file_context: Optional[str] = None,
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find relevant observations for current context.

        Args:
            query: The user's current query or task
            file_context: Current file being worked on
            branch: Current git branch

        Returns:
            List of suggestions with relevance reasons
        """
        # Build contextual query
        contextual_query = query

        if file_context:
            contextual_query = f"{query} (working on file: {file_context})"

        if branch:
            contextual_query = f"{contextual_query} (branch: {branch})"

        # Query Honcho for relevant observations
        try:
            response = self.peer.chat(
                f"What observations are relevant for: {contextual_query}? "
                "Include preferences, past decisions, and related experiences."
            )

            if not response or "don't have any information" in response.lower():
                return []

            # Parse response into suggestions
            return self._parse_suggestions(response, file_context, branch)

        except Exception as e:
            print(f"[ERROR] Query failed: {e}", file=sys.stderr)
            return []

    def _parse_suggestions(
        self,
        response: str,
        file_context: Optional[str],
        branch: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Parse the response into structured suggestions."""
        suggestions = []

        lines = response.split("\n")
        current_suggestion = None

        for line in lines:
            line = line.strip()

            # Check for list items
            if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
                if current_suggestion:
                    suggestions.append(current_suggestion)

                content = re.sub(r"^[-*•\d+\.\s]*", "", line).strip()
                current_suggestion = {
                    "content": content,
                    "relevance": self._determine_relevance(content, file_context, branch),
                    "metadata": {}
                }

            elif current_suggestion:
                # Additional context for current suggestion
                current_suggestion["content"] += " " + line

        if current_suggestion:
            suggestions.append(current_suggestion)

        return suggestions

    def _determine_relevance(
        self,
        content: str,
        file_context: Optional[str],
        branch: Optional[str]
    ) -> str:
        """Determine why this suggestion is relevant."""
        reasons = []

        content_lower = content.lower()

        if file_context:
            # Extract file extension/type
            ext = Path(file_context).suffix.lower()
            if ext in content_lower:
                reasons.append("matches file type")

            # Check if file name appears
            filename = Path(file_context).stem.lower()
            if filename and filename in content_lower:
                reasons.append("related to current file")

        if branch:
            if branch in content_lower:
                reasons.append("from this branch")

        if "prefer" in content_lower or "like" in content_lower or "use" in content_lower:
            reasons.append("preference match")

        if "decided" in content_lower or "chose" in content_lower:
            reasons.append("past decision")

        return ", ".join(reasons) if reasons else "semantic match"

    def detect_conflicts(self, current_action: str) -> List[Dict[str, Any]]:
        """
        Find observations that might conflict with current action.

        Returns a list of potential conflicts.
        """
        try:
            response = self.peer.chat(
                f"What preferences or decisions might conflict with: {current_action}? "
                "Focus on things like 'avoid', 'never use', 'prefer not', etc."
            )

            if not response or "don't have any information" in response.lower():
                return []

            # Parse conflicts
            conflicts = []
            lines = response.split("\n")

            for line in lines:
                line_lower = line.strip().lower()
                if any(word in line_lower for word in ["avoid", "never", "don't", "not", "prefer not"]):
                    conflicts.append({
                        "content": line.strip(),
                        "severity": self._assess_conflict_severity(line)
                    })

            return conflicts

        except Exception as e:
            print(f"[ERROR] Conflict detection failed: {e}", file=sys.stderr)
            return []

    def _assess_conflict_severity(self, text: str) -> str:
        """Assess the severity of a potential conflict."""
        text_lower = text.lower()

        if "never" in text_lower or "always" in text_lower:
            return "high"
        elif "avoid" in text_lower or "don't" in text_lower:
            return "medium"
        else:
            return "low"


def get_current_branch() -> Optional[str]:
    """Get the current git branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def format_suggestions(suggestions: List[Dict], verbose: bool = False) -> str:
    """Format suggestions for display."""
    if not suggestions:
        return "[INFO] No relevant suggestions found"

    lines = [
        f"[INFO] Found {len(suggestions)} relevant suggestion(s)",
        "=" * 60
    ]

    for i, suggestion in enumerate(suggestions, 1):
        content = suggestion.get("content", "")
        relevance = suggestion.get("relevance", "semantic match")

        lines.append(f"\n## Suggestion {i} (relevance: {relevance})")

        if len(content) > 300:
            content = content[:297] + "..."
        lines.append(content)

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_conflicts(conflicts: List[Dict]) -> str:
    """Format conflicts for display."""
    if not conflicts:
        return ""

    lines = [
        "\n⚠️  POTENTIAL CONFLICTS DETECTED",
        "-" * 40
    ]

    for conflict in conflicts:
        severity = conflict.get("severity", "low").upper()
        content = conflict.get("content", "")
        lines.append(f"  [{severity}] {content}")

    lines.append("-" * 40)
    return "\n".join(lines)


def main():
    """CLI for memory suggestions."""
    parser = argparse.ArgumentParser(
        description="Get proactive memory suggestions"
    )
    parser.add_argument(
        "--base-url", "-b",
        default=os.getenv("HONCHO_BASE_URL", "http://localhost:8000"),
        help="Honcho server URL"
    )
    parser.add_argument(
        "--workspace", "-w",
        default=os.getenv("HONCHO_WORKSPACE", "default"),
        help="Workspace ID"
    )
    parser.add_argument(
        "--peer", "-p",
        default=os.getenv("HONCHO_PEER_ID", "user"),
        help="Peer ID"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Query for suggestions"
    )
    parser.add_argument(
        "--context", "-c",
        help="Current file context"
    )
    parser.add_argument(
        "--branch", "-b",
        help="Current git branch (auto-detected if not specified)"
    )
    parser.add_argument(
        "--conflicts",
        action="store_true",
        help="Check for conflicting observations"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=5,
        help="Maximum suggestions"
    )

    args = parser.parse_args()

    # Auto-detect branch if not specified
    branch = args.branch
    if not branch:
        branch = get_current_branch()

    # Interactive mode if no query
    if not args.query and not args.conflicts:
        args.query = input("Enter your current task or query: ")

    print("=" * 60)
    print("Honcho Memory Suggestions")
    print("=" * 60)

    if branch:
        print(f"Branch: {branch}")
    if args.context:
        print(f"Context: {args.context}")

    print("-" * 60)

    try:
        suggester = MemorySuggester(
            args.base_url,
            args.workspace,
            args.peer
        )

        # Check for conflicts first
        if args.conflicts and args.query:
            conflicts = suggester.detect_conflicts(args.query)
            if conflicts:
                print(format_conflicts(conflicts))

        # Get suggestions
        if args.query:
            suggestions = suggester.suggest_for_context(
                args.query,
                args.context,
                branch
            )

            suggestions = suggestions[:args.limit]
            print(format_suggestions(suggestions))

    except Exception as e:
        print(f"\n[ERROR] Suggestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
