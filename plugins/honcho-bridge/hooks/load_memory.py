#!/usr/bin/env python3
"""
SessionStart hook: Load user's memory from Honcho.

Displays observations about the user at session start.
Includes smart workspace/peer detection if not configured.
"""

import os
import sys
import subprocess
from pathlib import Path

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


def get_git_username():
    """Get git username from config."""
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_folder_name():
    """Get current folder name."""
    return Path.cwd().name


def ensure_config():
    """Ensure .env exists with workspace and peer configured."""
    env_file = Path.cwd() / ".env"

    # If .env exists, nothing to do
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            if "HONCHO_WORKSPACE" in content and "HONCHO_PEER_ID" in content:
                return True, None

    # Smart detection
    workspace = get_folder_name()
    git_user = get_git_username()
    peer = git_user if git_user else os.getenv("USERNAME", "user")

    # Normalize peer ID (lowercase, no spaces)
    peer = peer.lower().replace(" ", "-")

    config = f"""# Honcho Bridge Configuration
# Auto-generated from folder name and git user

HONCHO_WORKSPACE={workspace}
HONCHO_PEER_ID={peer}
HONCHO_BASE_URL=http://localhost:8000
"""

    return False, (workspace, peer, config)


def load_user_memory() -> str:
    """Load and format user memory from Honcho."""
    if not HONCHO_AVAILABLE:
        return "[Honcho] honcho-ai not installed. Run: pip install honcho-ai"

    has_config, config_data = ensure_config()

    if not has_config and config_data:
        workspace, peer, config = config_data
        # Write the .env file
        env_file = Path.cwd() / ".env"
        with open(env_file, "w") as f:
            f.write(config)

        return f"""[Honcho] Configuration created!
  Workspace: {workspace}
  Peer ID: {peer}

Your memory will be stored under this workspace.
Edit .env to change these values."""

    # Read from .env or use defaults
    workspace = os.getenv("HONCHO_WORKSPACE", "default")
    peer_id = os.getenv("HONCHO_PEER_ID", "user")
    base_url = os.getenv("HONCHO_BASE_URL", "http://localhost:8000")

    try:
        client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )

        peer = client.peer(peer_id)

        # Query for observations about the user
        response = peer.chat("What do you know about this user? Summarize briefly.")

        if response and "don't have any information" not in response.lower():
            return f"[Honcho Memory] Workspace: {workspace} | Peer: {peer_id}\n\n{response}"
        else:
            return f"[Honcho] Workspace: {workspace} | Peer: {peer_id}\nNo observations yet. Use /honcho-store to save information."

    except Exception as e:
        return f"[Honcho] Connection failed: {e}"


if __name__ == "__main__":
    print(load_user_memory())
