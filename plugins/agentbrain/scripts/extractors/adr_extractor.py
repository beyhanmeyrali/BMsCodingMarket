"""
ADR Extractor for AgentBrain

Imports Architecture Decision Records as high-provenance memories.
ADRs document significant architectural decisions with context and rationale.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from skill_remember import skill_remember


# Common ADR locations
ADR_PATHS = [
    "doc/adr",
    "docs/adr",
    "docs/architecture",
    "docs/decisions",
    "adr",
    "decision-records",
    ".adr",
]


def find_adr_files(repo_root: Optional[Path] = None) -> List[Path]:
    """
    Find ADR files in the repository.

    Args:
        repo_root: Repository root (auto-detected if None)

    Returns:
        List of ADR file paths.
    """
    if repo_root is None:
        # Find git root
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            repo_root = Path(result.stdout.strip())
        except Exception:
            repo_root = Path.cwd()

    adr_files = []

    # Check common ADR locations
    for adr_path in ADR_PATHS:
        full_path = repo_root / adr_path
        if full_path.exists():
            # Find markdown files
            adr_files.extend(full_path.glob("**/*.md"))

    return adr_files


def parse_adr_frontmatter(content: str) -> Dict:
    """
    Parse ADR frontmatter to extract metadata.

    Args:
        content: ADR file content

    Returns:
        Frontmatter metadata.
    """
    import yaml

    # Try YAML frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except Exception:
            pass

    # Try Markdown-style ADR headers
    frontmatter = {}

    # Status
    status_match = re.search(r"Status:\s*(Accepted|Proposed|Deprecated|Superseded)", content, re.IGNORECASE)
    if status_match:
        frontmatter["status"] = status_match.group(1)

    # Date
    date_match = re.search(r"Date:\s*([\d-]+)", content)
    if date_match:
        frontmatter["date"] = date_match.group(1)

    # Decision
    decision_match = re.search(r"#\s+ADR\s+\d+[:\s-]+(.+?)(?:\n|$)", content, re.IGNORECASE)
    if decision_match:
        frontmatter["title"] = decision_match.group(1).strip()

    return frontmatter


def extract_decision(content: str) -> Optional[str]:
    """
    Extract the core decision statement from an ADR.

    Args:
        content: ADR file content

    Returns:
        Decision statement or None.
    """
    # Look for common patterns
    patterns = [
        r"## Decision\s+(.+?)(?:\n##|\n\n|\Z)",
        r"#\s+Decision\s+(.+?)(?:\n##|\n\n|\Z)",
        r"##\s+Decision\s*\n+(.+?)(?:\n##|\n\n)",
        r"###\s+Decision\s*\n+(.+?)(?:\n##|\n\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            decision = match.group(1).strip()
            # Clean up extra whitespace
            decision = re.sub(r"\s+", " ", decision)
            return decision[:500]

    return None


def extract_context(content: str) -> Optional[str]:
    """
    Extract the context from an ADR.

    Args:
        content: ADR file content

    Returns:
        Context statement or None.
    """
    patterns = [
        r"## Context\s+(.+?)(?:\n##|\n\nDecision)",
        r"## Background\s+(.+?)(?:\n##|\n\nDecision)",
        r"### Context\s+(.+?)(?:\n##|\n\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            context = match.group(1).strip()
            context = re.sub(r"\s+", " ", context)
            return context[:500]

    return None


def extract_consequences(content: str) -> List[str]:
    """
    Extract consequences from an ADR.

    Args:
        content: ADR file content

    Returns:
        List of consequences.
    """
    patterns = [
        r"## Consequences\s+(.+?)(?:\n##|\Z)",
        r"## Outcomes\s+(.+?)(?:\n##|\Z)",
        r"### Consequences\s+(.+?)(?:\n##|\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            # Extract bullet points
            bullets = re.findall(r"[-*]\s+(.+?)(?:\n|$)", text)
            if bullets:
                return [b.strip() for b in bullets if len(b.strip()) > 10]

    return []


def create_adr_memory(file_path: Path,
                      content: str,
                      scope: str = "project") -> str:
    """
    Create a memory from an ADR.

    Args:
        file_path: Path to ADR file
        content: ADR file content
        scope: Memory scope (default: project)

    Returns:
        Memory text.
    """
    frontmatter = parse_adr_frontmatter(content)
    decision = extract_decision(content)
    context = extract_context(content)
    consequences = extract_consequences(content)

    # Get title
    title = frontmatter.get("title") or file_path.stem.replace("-", " ").replace("_", " ")
    status = frontmatter.get("status", "Unknown")

    # Skip deprecated ADRs
    if status.lower() in ["deprecated", "superseded"]:
        return None

    # Build memory
    memory = f"# Architecture Decision: {title}\n\n"

    if context:
        memory += f"**Context:** {context}\n\n"

    if decision:
        memory += f"**Decision:** {decision}\n\n"

    memory += f"**Status:** {status}\n"
    memory += f"**Source:** {file_path.name}\n"

    if consequences:
        memory += f"\n**Consequences:**\n"
        for cons in consequences[:5]:
            memory += f"- {cons}\n"

    return memory


def import_adr(file_path: Path,
               scope: str = "project",
               auto_store: bool = False) -> Dict:
    """
    Import an ADR as a memory.

    Args:
        file_path: Path to ADR file
        scope: Memory scope
        auto_store: If True, automatically store the memory

    Returns:
        Import result.
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if deprecated
        frontmatter = parse_adr_frontmatter(content)
        status = frontmatter.get("status", "")
        if status.lower() in ["deprecated", "superseded"]:
            return {
                "file": str(file_path),
                "skipped": True,
                "reason": f"Status: {status}"
            }

        # Create memory
        memory_text = create_adr_memory(file_path, content, scope)

        if not memory_text:
            return {
                "file": str(file_path),
                "skipped": True,
                "reason": "Could not extract decision"
            }

        result = {
            "file": str(file_path),
            "title": frontmatter.get("title", file_path.stem),
            "status": status,
            "memory_preview": memory_text[:200] + "...",
        }

        if auto_store:
            try:
                store_result = skill_remember(memory_text)
                result["stored"] = True
                result["store_result"] = store_result[:100]
            except Exception as e:
                result["stored"] = False
                result["error"] = str(e)

        return result

    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e)
        }


def import_all_adrs(scope: str = "project",
                    auto_store: bool = False) -> Dict:
    """
    Import all ADRs from the repository.

    Args:
        scope: Memory scope
        auto_store: If True, automatically store memories

    Returns:
        Import results summary.
    """
    adr_files = find_adr_files()

    if not adr_files:
        return {
            "error": "No ADR files found. Checked: " + ", ".join(ADR_PATHS)
        }

    results = {
        "total_found": len(adr_files),
        "imported": 0,
        "skipped": 0,
        "failed": 0,
        "files": [],
    }

    for file_path in adr_files:
        result = import_adr(file_path, scope, auto_store)
        results["files"].append(result)

        if "error" in result:
            results["failed"] += 1
        elif result.get("skipped"):
            results["skipped"] += 1
        elif result.get("stored"):
            results["imported"] += 1

    return results


def print_results(results: Dict) -> None:
    """Print import results."""
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    print(f"\n{'='*60}")
    print("ADR Import Results")
    print(f"{'='*60}")

    if "total_found" in results:
        print(f"\nTotal ADRs found: {results['total_found']}")
        print(f"Imported: {results['imported']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Failed: {results['failed']}")

        print(f"\n--- Files ---")
        for f in results["files"]:
            if f.get("skipped"):
                print(f"[SKIP] {Path(f['file']).name}: {f.get('reason', '')}")
            elif "error" in f:
                print(f"[ERROR] {Path(f['file']).name}: {f['error']}")
            else:
                status = "[STORED]" if f.get("stored") else "[FOUND]"
                print(f"{status} {f['title']}")
    else:
        # Single file result
        if results.get("skipped"):
            print(f"[SKIP] {Path(results['file']).name}: {results.get('reason', '')}")
        elif "error" in results:
            print(f"[ERROR] {Path(results['file']).name}: {results['error']}")
        else:
            status = "[STORED]" if results.get("stored") else "[FOUND]"
            print(f"{status} {results['title']}")
            print(f"  {results['memory_preview']}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import Architecture Decision Records"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Specific ADR file to import"
    )
    parser.add_argument(
        "--scope",
        default="project",
        help="Memory scope (default: project)"
    )
    parser.add_argument(
        "--store",
        action="store_true",
        help="Automatically store as memories"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import all ADRs from repository"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if args.all:
        results = import_all_adrs(args.scope, args.store)
    elif args.file:
        results = import_adr(Path(args.file), args.scope, args.store)
    else:
        parser.print_help()
        return 1

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
