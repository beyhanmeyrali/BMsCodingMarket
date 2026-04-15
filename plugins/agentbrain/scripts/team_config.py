"""
Team Configuration Parser

Reads and parses .agentbrain/config.yml from repository root.
Provides team settings for memory scoping and promotion.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional


def find_repo_root() -> Optional[Path]:
    """
    Find the repository root directory.

    Returns:
        Path to repo root, or None if not in a git repo.
    """
    current_path = Path.cwd()

    # Search upward for .git directory
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").exists():
            return parent

    return None


def find_agentbrain_config(repo_root: Optional[Path] = None) -> Optional[Path]:
    """
    Find the .agentbrain/config.yml file.

    Args:
        repo_root: Repository root path (auto-detected if None)

    Returns:
        Path to config file, or None if not found.
    """
    if repo_root is None:
        repo_root = find_repo_root()

    if repo_root is None:
        return None

    config_path = repo_root / ".agentbrain" / "config.yml"
    return config_path if config_path.exists() else None


def load_team_config(config_path: Optional[Path] = None) -> Dict:
    """
    Load team configuration from .agentbrain/config.yml.

    Args:
        config_path: Path to config file (auto-detected if None)

    Returns:
        Configuration dict with defaults applied.
    """
    # Default configuration
    default_config = {
        "team_id": "",
        "org_id": "",
        "memory_types": [],
        "review_required": False,
        "codeowners": [],
        "default_scope": None,
        "auto_promote": {
            "enabled": False,
            "threshold": 5,
        },
    }

    if config_path is None:
        config_path = find_agentbrain_config()

    if config_path is None:
        return default_config

    try:
        with open(config_path, encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}

        # Merge with defaults
        config = {**default_config, **user_config}

        # Handle nested auto_promote
        if "auto_promote" in user_config:
            config["auto_promote"] = {**default_config["auto_promote"], **user_config["auto_promote"]}

        return config

    except Exception as e:
        # Return defaults on error
        return default_config


def get_team_memory_dir(repo_root: Optional[Path] = None) -> Optional[Path]:
    """
    Get the directory for team memory files.

    Args:
        repo_root: Repository root path (auto-detected if None)

    Returns:
        Path to team memory directory, or None if not configured.
    """
    if repo_root is None:
        repo_root = find_repo_root()

    if repo_root is None:
        return None

    memory_dir = repo_root / ".agentbrain" / "memory"
    return memory_dir if memory_dir.exists() else None


def get_team_scopes(config: Optional[Dict] = None) -> List[str]:
    """
    Get list of allowed scopes based on team configuration.

    Args:
        config: Team configuration (auto-loaded if None)

    Returns:
        List of scope strings (e.g., ["team:platform", "project:myrepo"]).
    """
    if config is None:
        config = load_team_config()

    scopes = []

    # Add team scope if configured
    team_id = config.get("team_id", "")
    if team_id:
        scopes.append(f"team:{team_id}")

    # Add org scope if configured
    org_id = config.get("org_id", "")
    if org_id:
        scopes.append(f"org:{org_id}")

    # Add project scope if in a repo
    repo_root = find_repo_root()
    if repo_root:
        project_name = repo_root.name
        scopes.append(f"project:{project_name}")

    return scopes


def get_repo_memory_files(repo_root: Optional[Path] = None) -> List[Path]:
    """
    Get all memory files in the repository's .agentbrain/memory directory.

    Args:
        repo_root: Repository root path (auto-detected if None)

    Returns:
        List of memory file paths.
    """
    memory_dir = get_team_memory_dir(repo_root)

    if not memory_dir:
        return []

    return list(memory_dir.glob("**/*.md"))


def is_review_required(config: Optional[Dict] = None) -> bool:
    """
    Check if review is required for team memories.

    Args:
        config: Team configuration (auto-loaded if None)

    Returns:
        True if PR review is required.
    """
    if config is None:
        config = load_team_config()

    return config.get("review_required", False)


def get_codeowners(config: Optional[Dict] = None) -> List[str]:
    """
    Get list of codeowners for team memory review.

    Args:
        config: Team configuration (auto-loaded if None)

    Returns:
        List of codeowner usernames.
    """
    if config is None:
        config = load_team_config()

    return config.get("codeowners", [])


def main():
    """CLI for testing team config."""
    import argparse

    parser = argparse.ArgumentParser(description="AgentBrain team configuration")
    parser.add_argument("--show", action="store_true", help="Show current config")
    parser.add_argument("--scopes", action="store_true", help="Show allowed scopes")
    parser.add_argument("--files", action="store_true", help="Show repo memory files")
    parser.add_argument("--dir", type=str, help="Use specific repo directory")

    args = parser.parse_args()

    if args.dir:
        os.chdir(args.dir)

    if args.show:
        config = load_team_config()
        import json
        print(json.dumps(config, indent=2))

    elif args.scopes:
        scopes = get_team_scopes()
        print("Allowed scopes:")
        for scope in scopes:
            print(f"  - {scope}")

    elif args.files:
        files = get_repo_memory_files()
        print(f"Repo memory files ({len(files)}):")
        for file in files:
            print(f"  - {file.relative_to(find_repo_root())}")

    else:
        print("AgentBrain Team Configuration")
        print("=" * 40)
        config_path = find_agentbrain_config()
        if config_path:
            print(f"Config found: {config_path}")
        else:
            print("No .agentbrain/config.yml found in this repository")


if __name__ == "__main__":
    main()
