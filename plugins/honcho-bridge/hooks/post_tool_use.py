#!/usr/bin/env python3
"""
PostToolUse hook: Capture tool usage patterns and results.

Features:
- Track which tools are used (Read, Edit, Bash, etc.)
- Capture git changes from tool results
- Build tech stack detection from files accessed
- Store usage patterns for future learning
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

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

# Add privacy module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "privacy"))
try:
    from redact import PrivacyFilter, is_privacy_enabled
    PRIVACY_AVAILABLE = True
except ImportError:
    PRIVACY_AVAILABLE = False


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


# File extension to tech stack mapping
EXTENSION_MAP = {
    # Python
    ".py": "python",
    ".pyi": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "react",
    ".ts": "typescript",
    ".tsx": "react",
    ".mjs": "javascript",
    ".cjs": "javascript",
    # Web
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    # Backend
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".php": "php",
    # Config/Data
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown",
    # Shell
    ".sh": "shell",
    ".bash": "bash",
    ".zsh": "zsh",
    ".ps1": "powershell",
    # Database
    ".sql": "sql",
    # Other
    ".rb": "ruby",
    ".swift": "swift",
    ".dart": "dart",
    ".lua": "lua",
    ".r": "r",
}


# Special file names for tech detection
SPECIAL_FILES = {
    "package.json": "nodejs",
    "yarn.lock": "nodejs",
    "package-lock.json": "nodejs",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "Pipfile": "python",
    "poetry.lock": "python",
    "go.mod": "go",
    "go.sum": "go",
    "Cargo.toml": "rust",
    "Cargo.lock": "rust",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "Gemfile": "ruby",
    "composer.json": "php",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "docker-compose.yaml": "docker",
    "Makefile": "make",
    "CMakeLists.txt": "cmake",
    ".gitignore": "git",
}


def detect_tech_from_path(file_path: str) -> Optional[str]:
    """Detect technology from file path."""
    path = Path(file_path)
    ext = path.suffix.lower()
    name = path.name

    # Check special files first
    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]

    # Check extension
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]

    return None


def extract_file_paths_from_tool_use(tool_name: str, tool_input: Dict, tool_result: Any) -> List[str]:
    """
    Extract file paths from tool usage.

    Returns list of file paths that were accessed or modified.
    """
    paths = []

    if tool_name == "Read":
        paths.append(tool_input.get("file_path", ""))

    elif tool_name == "Write":
        paths.append(tool_input.get("file_path", ""))

    elif tool_name == "Edit":
        paths.append(tool_input.get("file_path", ""))

    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        if pattern:
            # Store the pattern itself
            paths.append(f"glob:{pattern}")

    elif tool_name == "Grep":
        path = tool_input.get("path", "")
        pattern = tool_input.get("pattern", "")
        if path:
            paths.append(f"grep:{path}")
        if pattern:
            paths.append(f"grep_pattern:{pattern[:50]}")

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        # Extract file paths from common commands
        if command:
            # Git operations
            if "git diff" in command or "git status" in command:
                paths.append("git:status")
            elif "git log" in command:
                paths.append("git:log")
            # File operations
            elif "cat " in command or "less " in command or "more " in command:
                # Try to extract file path
                parts = command.split()
                for i, part in enumerate(parts):
                    if part in ["cat", "less", "more"] and i + 1 < len(parts):
                        paths.append(parts[i + 1])

    elif tool_name == "Agent":
        # Agent dispatch - store the agent type and description
        description = tool_input.get("description", "")
        subagent_type = tool_input.get("subagent_type", "")
        paths.append(f"agent:{subagent_type}")

    return [p for p in paths if p]


def extract_tech_stack_from_paths(paths: List[str]) -> List[str]:
    """Extract unique tech stack from file paths."""
    tech_set = set()

    for path in paths:
        tech = detect_tech_from_path(path)
        if tech:
            tech_set.add(tech)

    return sorted(list(tech_set))


def track_tool_usage(tool_name: str, tool_input: Dict, tool_result: Any, context: Dict) -> Dict:
    """
    Track tool usage and extract insights.

    Returns a summary of the tool usage with detected tech stack and patterns.
    """
    summary = {
        "tool": tool_name,
        "timestamp": datetime.now().isoformat(),
        "files_accessed": [],
        "tech_detected": [],
        "patterns": [],
        "success": None,
    }

    # Extract file paths
    paths = extract_file_paths_from_tool_use(tool_name, tool_input, tool_result)
    summary["files_accessed"] = paths

    # Detect tech stack
    tech = extract_tech_stack_from_paths(paths)
    summary["tech_detected"] = tech

    # Determine success/failure
    if isinstance(tool_result, dict):
        # Check for errors
        if "error" in tool_result:
            summary["success"] = False
            summary["error"] = str(tool_result["error"])[:100]
        else:
            summary["success"] = True
    elif isinstance(tool_result, str) and "Error" in tool_result:
        summary["success"] = False
        summary["error"] = tool_result[:100]
    else:
        summary["success"] = True

    # Detect patterns
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if "test" in command.lower():
            summary["patterns"].append("testing")
        if "build" in command.lower():
            summary["patterns"].append("building")
        if "deploy" in command.lower():
            summary["patterns"].append("deploying")
        if "git " in command:
            summary["patterns"].append("git_operations")

    elif tool_name in ["Read", "Edit", "Write"]:
        if any(p.endswith(".test.") or p.endswith(".spec.") for p in paths):
            summary["patterns"].append("test_file_access")
        if any("test" in p.lower() for p in paths):
            summary["patterns"].append("test_directory_access")

    elif tool_name == "Agent":
        summary["patterns"].append("delegation")

    return summary


def store_tool_usage_summary(summary: Dict, base_url: str, workspace: str, peer_id: str) -> bool:
    """Store tool usage summary to Honcho for learning patterns."""
    if not HONCHO_AVAILABLE:
        return False

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id, metadata={
            "name": "User",
            "peer_type": "user"
        })

        # Store in a special session for tool patterns
        session_id = "tool-patterns"
        session = client.session(session_id)

        # Create a summary message
        tech_str = ", ".join(summary["tech_detected"]) if summary["tech_detected"] else "none"
        files_str = ", ".join(summary["files_accessed"][:3])  # First 3 files
        if len(summary["files_accessed"]) > 3:
            files_str += f" (+{len(summary['files_accessed']) - 3} more)"

        message_content = (
            f"[TOOL USAGE] Used {summary['tool']}\n"
            f"Tech: {tech_str}\n"
            f"Files: {files_str}\n"
            f"Success: {summary['success']}"
        )

        if summary.get("patterns"):
            message_content += f"\nPatterns: {', '.join(summary['patterns'])}"

        msg = peer.message(message_content)
        session.add_messages([msg])

        return True

    except Exception as e:
        print(f"[Honcho] Failed to store tool usage: {e}", file=sys.stderr)
        return False


def process_tool_use(tool_name: str, tool_input: Dict, tool_result: Any) -> Dict:
    """
    Process a tool use event.

    Args:
        tool_name: Name of the tool used
        tool_input: Input parameters to the tool
        tool_result: Result returned by the tool

    Returns:
        Processing summary
    """
    # Check if opted out
    if os.getenv("HONCHO_SESSION_OPT_OUT", "false").lower() == "true":
        return {"opted_out": True}

    # Capture context
    context = {
        "timestamp": datetime.now().isoformat(),
        "cwd": str(Path.cwd()),
        "folder": Path.cwd().name,
    }

    # Track tool usage
    summary = track_tool_usage(tool_name, tool_input, tool_result, context)

    # Store to Honcho if configured
    if os.getenv("HONCHO_TRACK_TOOL_USAGE", "true").lower() == "true":
        base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")
        workspace = os.getenv("HONCHO_WORKSPACE", "default")
        peer_id = os.getenv("HONCHO_PEER_ID", "user")

        store_tool_usage_summary(summary, base_url, workspace, peer_id)

    return summary


def main():
    """Main entry point for the hook."""
    # Tool info may come from environment variables or stdin
    tool_name = os.getenv("HONCHO_TOOL_NAME", "")
    tool_input_str = os.getenv("HONCHO_TOOL_INPUT", "{}")
    tool_result_str = os.getenv("HONCHO_TOOL_RESULT", "{}")

    # Try to read from stdin if no env vars
    if not tool_name and not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            tool_name = data.get("tool_name", "")
            tool_input_str = data.get("tool_input", "{}")
            tool_result_str = data.get("tool_result", "{}")
        except json.JSONDecodeError:
            pass

    # If still no tool info, just display status
    if not tool_name:
        print("[Honcho] PostToolUse hook ready")
        print(f"  Tool tracking: {os.getenv('HONCHO_TRACK_TOOL_USAGE', 'true')}")
        return

    try:
        tool_input = json.loads(tool_input_str) if isinstance(tool_input_str, str) else tool_input_str
        tool_result = json.loads(tool_result_str) if isinstance(tool_result_str, str) else tool_result_str
    except json.JSONDecodeError:
        tool_input = {}
        tool_result = {}

    result = process_tool_use(tool_name, tool_input, tool_result)

    if result.get("opted_out"):
        print("[Honcho] Session opted out of tool tracking")
        return

    # Output summary
    if result.get("tech_detected"):
        print(f"[Honcho] Detected tech: {', '.join(result['tech_detected'])}")

    # Only print for significant tool usage
    if tool_name in ["Read", "Write", "Edit", "Bash", "Agent"]:
        if result.get("files_accessed"):
            print(f"[Honcho] {tool_name}: {len(result['files_accessed'])} file(s)")


if __name__ == "__main__":
    main()
