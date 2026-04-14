#!/usr/bin/env python3
"""
UserPromptSubmit hook: Capture and process user prompts before they go to Claude.

Features:
- Critical fact detection (REMEMBER:, never forget, important:)
- Privacy redaction
- Context capture for tagging
- Immediate storage of critical facts (bypasses deriver latency)
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

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
    from redact import PrivacyFilter, is_privacy_enabled, redact
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


# Critical fact detection patterns
CRITICAL_PATTERNS = [
    r"\bREMEMBER\s*:?\s*(.+)",
    r"\bnever forget\s*:?\s*(.+)",
    r"\bimportant\s*:?\s*(.+)",
    r"\bNOTE\s*:?\s*(.+)",
    r"\bKEY\s+FACT\s*:?\s*(.+)",
    r"\bALWAYS\s*:?\s*(.+)",
    r"\bNEVER\s*:?\s*(.+)",
]


def detect_critical_facts(text: str) -> list:
    """
    Detect critical facts that should be stored immediately.

    Returns list of (match, fact_content) tuples.
    """
    facts = []
    for pattern in CRITICAL_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            fact_content = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else match.group(0).strip()
            if len(fact_content) > 5:  # Minimum meaningful length
                facts.append({
                    "pattern": pattern,
                    "full_match": match.group(0),
                    "content": fact_content,
                    "position": match.start(),
                })
    return facts


def capture_git_context() -> dict:
    """Capture current git context for tagging."""
    context = {
        "branch": None,
        "commit": None,
        "status": [],
        "root": None,
    }

    try:
        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            context["branch"] = result.stdout.strip()

        # Get current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            context["commit"] = result.stdout.strip()[:8]

        # Get git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            context["root"] = result.stdout.strip()

        # Get status (modified files)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            context["status"] = result.stdout.strip().split("\n") if result.stdout.strip() else []

    except Exception:
        pass

    return context


def detect_tech_stack() -> list:
    """Detect project tech stack from common files."""
    tech_stack = []
    cwd = Path.cwd()

    # Check for Python
    if (cwd / "requirements.txt").exists() or (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists():
        tech_stack.append("python")

    # Check for Node.js
    if (cwd / "package.json").exists() or (cwd / "yarn.lock").exists() or (cwd / "package-lock.json").exists():
        tech_stack.append("nodejs")

    # Check for Go
    if (cwd / "go.mod").exists():
        tech_stack.append("go")

    # Check for Rust
    if (cwd / "Cargo.toml").exists():
        tech_stack.append("rust")

    # Check for Java/Kotlin
    if (cwd / "pom.xml").exists() or (cwd / "build.gradle").exists() or (cwd / "build.gradle.kts").exists():
        tech_stack.append("jvm")

    # Check for Docker
    if (cwd / "Dockerfile").exists() or (cwd / "docker-compose.yml").exists() or (cwd / "docker-compose.yaml").exists():
        tech_stack.append("docker")

    return tech_stack


def capture_context() -> dict:
    """Capture all context for tagging."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cwd": str(Path.cwd()),
        "folder_name": Path.cwd().name,
        "git": capture_git_context(),
        "tech_stack": detect_tech_stack(),
    }


def store_critical_fact_immediately(fact: str, context: dict, base_url: str, workspace: str, peer_id: str) -> bool:
    """
    Store a critical fact immediately to Honcho.

    Bypasses the deriver queue for immediate availability.
    Stores as a special "critical" message type.
    """
    if not HONCHO_AVAILABLE:
        return False

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        # Create/get peer
        peer = client.peer(peer_id, metadata={
            "name": "User",
            "peer_type": "user"
        })

        # Create special session for critical facts
        session_id = "critical-facts"
        session = client.session(session_id)

        # Store with special metadata
        message_content = f"[CRITICAL FACT] {fact}"

        # Add context metadata
        metadata = {
            "type": "critical_fact",
            "immediate": True,
            "timestamp": context["timestamp"],
            "folder": context["folder_name"],
        }

        if context.get("git", {}).get("branch"):
            metadata["branch"] = context["git"]["branch"]

        if context.get("tech_stack"):
            metadata["tech_stack"] = ",".join(context["tech_stack"])

        # Store the message
        msg = peer.message(message_content)
        session.add_messages([msg])

        return True

    except Exception as e:
        print(f"[Honcho] Failed to store critical fact: {e}", file=sys.stderr)
        return False


def process_user_prompt(content: str) -> dict:
    """
    Process user prompt for critical facts and apply privacy filtering.

    Returns processing result with detected facts, redactions, and storage status.
    """
    # Check if session is opted out
    if os.getenv("HONCHO_SESSION_OPT_OUT", "false").lower() == "true":
        return {"opted_out": True}

    result = {
        "detected_facts": [],
        "redactions": [],
        "stored_immediately": [],
        "context": None,
        "privacy_enabled": is_privacy_enabled() if PRIVACY_AVAILABLE else False,
    }

    # Capture context
    context = capture_context()
    result["context"] = {
        "folder": context["folder_name"],
        "branch": context.get("git", {}).get("branch"),
        "tech_stack": context.get("tech_stack", []),
    }

    # Detect critical facts
    facts = detect_critical_facts(content)
    result["detected_facts"] = [f["content"] for f in facts]

    # Apply privacy redaction
    if PRIVACY_AVAILABLE and result["privacy_enabled"]:
        redacted_content, secrets = redact(content)
        result["redactions"] = [
            {"type": s["type"], "original": s["original"][:30] + "..."}
            for s in secrets
        ]
    else:
        redacted_content = content

    # Store critical facts immediately
    base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")
    workspace = os.getenv("HONCHO_WORKSPACE", "default")
    peer_id = os.getenv("HONCHO_PEER_ID", "user")

    for fact in facts:
        stored = store_critical_fact_immediately(
            fact["content"],
            context,
            base_url,
            workspace,
            peer_id
        )
        if stored:
            result["stored_immediately"].append(fact["content"])

    return result


def main():
    """Main entry point for the hook."""
    # The hook may receive content via stdin or environment variable
    content = os.getenv("HONCHO_USER_PROMPT", "")

    # If no content, read from stdin
    if not content and not sys.stdin.isatty():
        content = sys.stdin.read()

    # If still no content, just display status
    if not content:
        print("[Honcho] UserPromptSubmit hook ready")
        print(f"  Privacy enabled: {is_privacy_enabled() if PRIVACY_AVAILABLE else 'N/A'}")
        print(f"  Immediate store: {os.getenv('HONCHO_IMMEDIATE_STORE', 'true')}")
        return

    result = process_user_prompt(content)

    # Output results (will be captured by Claude Code)
    if result.get("opted_out"):
        print("[Honcho] Session opted out of memory storage")
        return

    if result["detected_facts"]:
        print(f"[Honcho] Detected {len(result['detected_facts'])} critical fact(s)")
        for fact in result["detected_facts"]:
            print(f"  → {fact[:80]}")

    if result["stored_immediately"]:
        print(f"[Honcho] Stored {len(result['stored_immediately'])} fact(s) immediately")

    if result["redactions"]:
        print(f"[Honcho] Redacted {len(result['redactions'])} sensitive item(s)")
        for redaction in result["redactions"]:
            print(f"  → {redaction['type']}: {redaction['original']}")


if __name__ == "__main__":
    main()
