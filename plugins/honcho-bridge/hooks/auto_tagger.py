#!/usr/bin/env python3
"""
Context-aware auto-tagging module for Honcho memory.

Captures context information (git, tech stack, project type) for tagging memories.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def load_env_config():
    """Load configuration from .env file in current directory."""
    env_file = Path.cwd() / ".env"
    config = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def capture_git_context() -> Dict:
    """Capture current git context for tagging."""
    context = {
        "branch": None,
        "commit": None,
        "commit_short": None,
        "status": [],
        "staged": [],
        "modified": [],
        "untracked": [],
        "root": None,
        "remote": None,
    }

    try:
        cwd = os.getcwd()

        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )
        if result.returncode == 0:
            context["branch"] = result.stdout.strip()

        # Get current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )
        if result.returncode == 0:
            full_hash = result.stdout.strip()
            context["commit"] = full_hash
            context["commit_short"] = full_hash[:8] if len(full_hash) >= 8 else full_hash

        # Get git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )
        if result.returncode == 0:
            context["root"] = result.stdout.strip()

        # Get remote origin
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )
        if result.returncode == 0:
            context["remote"] = result.stdout.strip()

        # Get status (porcelain format for parsing)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                status_code = line[:2]
                file_path = line[3:]

                context["status"].append(file_path)

                if status_code[0] in ["M", "A", "D", "R"]:
                    context["staged"].append(file_path)
                if status_code[1] in ["M"]:
                    context["modified"].append(file_path)
                if status_code == "??":
                    context["untracked"].append(file_path)

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    return context


# File extension to tech stack mapping
EXTENSION_MAP = {
    # Python
    ".py": "python",
    ".pyi": "python",
    ".ipynb": "jupyter",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "react",
    ".ts": "typescript",
    ".tsx": "react",
    ".mjs": "javascript",
    ".cjs": "javascript",
    # Web
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".styl": "stylus",
    # Backend
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".cs": "csharp",
    ".fs": "fsharp",
    ".vb": "vb",
    ".php": "php",
    # Config/Data
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "config",
    ".conf": "config",
    # Shell
    ".sh": "shell",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".psm1": "powershell",
    # Database
    ".sql": "sql",
    # Other
    ".rb": "ruby",
    ".swift": "swift",
    ".dart": "dart",
    ".lua": "lua",
    ".r": "r",
    ".R": "r",
    ".m": "matlab",
    ".jl": "julia",
    ".scala": "scala",
    ".clj": "clojure",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".nim": "nim",
    ".zig": "zig",
    ".v": "v",
    # Templates
    ".hbs": "handlebars",
    ".mustache": "mustache",
    ".ejs": "ejs",
    ".pug": "pug",
    ".haml": "haml",
}


# Special file names for tech detection
SPECIAL_FILES = {
    # JavaScript/Node
    "package.json": "nodejs",
    "yarn.lock": "nodejs",
    "package-lock.json": "nodejs",
    "pnpm-lock.yaml": "nodejs",
    "bun.lockb": "bun",
    # Python
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "Pipfile": "python",
    "poetry.lock": "python",
    "pipenv.lock": "python",
    "tox.ini": "python",
    ".python-version": "python",
    # Go
    "go.mod": "go",
    "go.sum": "go",
    # Rust
    "Cargo.toml": "rust",
    "Cargo.lock": "rust",
    "Rustfile": "rust",
    # Java
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "settings.gradle": "gradle",
    "gradle.properties": "gradle",
    # Ruby
    "Gemfile": "ruby",
    "gemfile.lock": "ruby",
    ".ruby-version": "ruby",
    # PHP
    "composer.json": "php",
    "composer.lock": "php",
    # Docker
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "docker-compose.yaml": "docker",
    "Dockerfile.prod": "docker",
    # Other
    "Makefile": "make",
    "CMakeLists.txt": "cmake",
    "meson.build": "meson",
    "Vagrantfile": "vagrant",
    "terraform.tf": "terraform",
    "main.tf": "terraform",
    "helm": "helm",
    "Chart.yaml": "helm",
    "values.yaml": "helm",
    # Config
    ".gitignore": "git",
    ".gitattributes": "git",
    ".env.example": "env",
    ".editorconfig": "editorconfig",
    # Testing
    "jest.config.js": "jest",
    "vitest.config.ts": "vitest",
    "pytest.ini": "pytest",
    "tox.ini": "tox",
    ".eslintrc": "eslint",
    ".prettierrc": "prettier",
}


def detect_tech_from_files(cwd: Path) -> List[str]:
    """Detect tech stack by scanning project files."""
    tech_set = set()

    # Check special files in root
    for filename, tech in SPECIAL_FILES.items():
        if (cwd / filename).exists():
            tech_set.add(tech)

    # Scan some common directories for file extensions
    for root_dir in ["src", "lib", "app", "components", "services", "utils"]:
        root_path = cwd / root_dir
        if not root_path.exists():
            continue

        # Limit scan to avoid performance issues
        count = 0
        max_files = 100

        for file_path in root_path.rglob("*"):
            if count >= max_files:
                break
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in EXTENSION_MAP:
                    tech_set.add(EXTENSION_MAP[ext])
                    count += 1

    return sorted(list(tech_set))


def detect_tech_stack() -> List[str]:
    """Detect project tech stack from current directory."""
    cwd = Path.cwd()

    # Quick check for special files
    tech_set = set()

    for filename, tech in SPECIAL_FILES.items():
        if (cwd / filename).exists():
            tech_set.add(tech)

    # Check for common directories
    for dir_name in ["src", "lib", "app", "scripts", "test", "tests", "__tests__"]:
        if (cwd / dir_name).exists():
            # Recursively detect from directory
            tech_set.update(detect_tech_from_files(cwd / dir_name))
            break

    return sorted(list(tech_set))


def detect_project_type() -> str:
    """Classify project type based on structure and files."""
    cwd = Path.cwd()

    # Check for web frameworks
    if (cwd / "next.config.js").exists() or (cwd / "next.config.mjs").exists():
        return "nextjs"
    if (cwd / "nuxt.config.js").exists() or (cwd / "nuxt.config.ts").exists():
        return "nuxt"
    if (cwd / "vue.config.js").exists():
        return "vue"
    if (cwd / "angular.json").exists():
        return "angular"
    if (cwd / "remix.config.js").exists():
        return "remix"
    if (cwd / "svelte.config.js").exists():
        return "svelte"

    # Check for mobile
    if (cwd / "android").exists() and (cwd / "ios").exists():
        return "react-native"
    if (cwd / "pubspec.yaml").exists():
        return "flutter"

    # Check for backend frameworks
    if (cwd / "manage.py").exists():
        return "django"
    if (cwd / "app.py").exists() or (cwd / "main.py").exists():
        if (cwd / "requirements.txt").exists():
            return "python-backend"
    if (cwd / "main.go").exists():
        return "go-backend"
    if (cwd / "main.rs").exists() or (cwd / "Cargo.toml").exists():
        return "rust-service"

    # Check for CLI tools
    if (cwd / "Cargo.toml").exists() and (cwd / "src").exists() and (cwd / "src" / "main.rs").exists():
        return "rust-cli"

    # Check for libraries
    if (cwd / "pyproject.toml").exists():
        content = (cwd / "pyproject.toml").read_text()
        if "[tool.poetry]" in content or "[project]" in content:
            return "python-library"

    # Default
    tech = detect_tech_stack()
    if "python" in tech:
        return "python-project"
    if "nodejs" in tech:
        return "javascript-project"
    if "go" in tech:
        return "go-project"

    return "general"


def capture_all_context() -> Dict:
    """Collect all context tags for memory storage."""
    cwd = Path.cwd()

    context = {
        "timestamp": datetime.now().isoformat(),
        "cwd": str(cwd),
        "folder_name": cwd.name,
        "parent_folder": cwd.parent.name if cwd.parent != cwd else None,
        "git": capture_git_context(),
        "tech_stack": detect_tech_stack(),
        "project_type": detect_project_type(),
    }

    return context


def format_context_tags(context: Dict) -> Dict[str, str]:
    """
    Format context as flat tag dictionary for metadata.

    Returns a dict suitable for Honcho peer/session metadata.
    """
    tags = {}

    # Basic info
    tags["folder"] = context.get("folder_name", "unknown")

    # Git info
    git = context.get("git", {})
    if git.get("branch"):
        tags["branch"] = git["branch"]
    if git.get("commit_short"):
        tags["commit"] = git["commit_short"]

    # Tech stack
    tech = context.get("tech_stack", [])
    if tech:
        tags["tech_stack"] = ",".join(tech)

    # Project type
    project_type = context.get("project_type")
    if project_type:
        tags["project_type"] = project_type

    return tags


def main():
    """CLI for testing context capture."""
    import json

    print("=" * 60)
    print("Honcho Context Tagger")
    print("=" * 60)

    context = capture_all_context()

    print("\n## Git Context")
    git = context["git"]
    if git["branch"]:
        print(f"Branch: {git['branch']}")
    if git["commit_short"]:
        print(f"Commit: {git['commit_short']}")
    if git["staged"]:
        print(f"Staged: {len(git['staged'])} file(s)")
    if git["modified"]:
        print(f"Modified: {len(git['modified'])} file(s)")

    print("\n## Tech Stack")
    tech = context["tech_stack"]
    if tech:
        for t in tech:
            print(f"  - {t}")
    else:
        print("  (none detected)")

    print("\n## Project Type")
    print(f"  {context['project_type']}")

    print("\n## Formatted Tags (for metadata)")
    tags = format_context_tags(context)
    print(json.dumps(tags, indent=2))


if __name__ == "__main__":
    main()
