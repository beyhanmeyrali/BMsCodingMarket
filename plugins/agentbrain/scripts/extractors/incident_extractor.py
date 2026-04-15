"""
Incident Extractor for AgentBrain

Parses incident postmortems to extract "never do X" rules and lessons learned.
Incidents are high-provenance sources of what to avoid.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from skill_remember import skill_remember


# Common incident postmortem locations
INCIDENT_PATHS = [
    "docs/incidents",
    "docs/postmortems",
    "docs/post-mortems",
    "incidents",
    "postmortems",
    ".incident-reports",
]


# Keywords that signal important lessons
LESSON_KEYWORDS = [
    "root cause",
    "lessons learned",
    "takeaways",
    "prevent",
    "avoid",
    "never",
    "should not",
    "recommendation",
    "action item",
    "fix",
    "mitigation",
    "resolution",
]

# Keywords that signal failures
FAILURE_KEYWORDS = [
    "mistake",
    "error",
    "failure",
    "outage",
    "downtime",
    "crash",
    "bug",
    "incident",
    "issue",
    "problem",
]


def find_incident_files(repo_root: Optional[Path] = None) -> List[Path]:
    """
    Find incident postmortem files in the repository.

    Args:
        repo_root: Repository root (auto-detected if None)

    Returns:
        List of incident file paths.
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

    incident_files = []

    # Check common incident locations
    for incident_path in INCIDENT_PATHS:
        full_path = repo_root / incident_path
        if full_path.exists():
            incident_files.extend(full_path.glob("**/*.md"))

    return incident_files


def extract_incident_metadata(content: str) -> Dict:
    """
    Extract metadata from incident postmortem.

    Args:
        content: Incident file content

    Returns:
        Metadata dictionary.
    """
    metadata = {}

    # Try YAML frontmatter
    import yaml
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except Exception:
            pass

    # Extract if not in frontmatter
    if "title" not in metadata:
        title_match = re.search(r"#\s+(.+?)(?:\n|$)", content)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

    if "date" not in metadata:
        date_match = re.search(r"Date:\s*([\d-]+)", content, re.IGNORECASE)
        if date_match:
            metadata["date"] = date_match.group(1)

    if "severity" not in metadata:
        sev_match = re.search(r"Severity?\s*:?\s*(\w+)", content, re.IGNORECASE)
        if sev_match:
            metadata["severity"] = sev_match.group(1)

    return metadata


def extract_root_cause(content: str) -> Optional[str]:
    """
    Extract root cause from incident postmortem.

    Args:
        content: Incident file content

    Returns:
        Root cause statement or None.
    """
    patterns = [
        r"## Root Cause\s*(.+?)(?:\n##|\n\n)",
        r"## Root\s*Cause\s*(.+?)(?:\n##|\n\n)",
        r"### Root Cause\s*(.+?)(?:\n##|\n\n)",
        r"## Cause\s*(.+?)(?:\n##|\n\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            cause = match.group(1).strip()
            cause = re.sub(r"\s+", " ", cause)
            return cause[:500]

    return None


def extract_lessons(content: str) -> List[str]:
    """
    Extract lessons learned from incident postmortem.

    Args:
        content: Incident file content

    Returns:
        List of lesson statements.
    """
    lessons = []

    patterns = [
        r"## Lessons Learned\s*(.+?)(?:\n##|\Z)",
        r"## Lessons\s*(.+?)(?:\n##|\Z)",
        r"## Takeaways\s*(.+?)(?:\n##|\Z)",
        r"## Recommendations\s*(.+?)(?:\n##|\Z)",
        r"## Action Items\s*(.+?)(?:\n##|\Z)",
        r"## Prevention\s*(.+?)(?:\n##|\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            # Extract bullet points
            bullets = re.findall(r"[-*]\s+(.+?)(?:\n|$)", text)
            if bullets:
                lessons.extend([b.strip() for b in bullets if len(b.strip()) > 10])

    return lessons


def extract_negative_rules(content: str) -> List[str]:
    """
    Extract negative rules (what NOT to do) from incident.

    Args:
        content: Incident file content

    Returns:
        List of negative rule statements.
    """
    rules = []

    # Look for "never", "avoid", "should not" patterns
    patterns = [
        r"(Never|Avoid|Don't|Do not)\s+[\w\s,]+?(?:\.|;|\n)",
        r"(should not|must not)\s+[\w\s,]+?(?:\.|;|\n)",
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            rule = match.group(0).strip()
            if len(rule) > 15 and len(rule) < 200:
                rules.append(rule)

    return rules[:10]  # Limit to 10 rules


def create_lesson_memory(title: str,
                         lesson: str,
                         source_file: str) -> str:
    """
    Create a memory from a lesson learned.

    Args:
        title: Incident title
        lesson: Lesson statement
        source_file: Source file name

    Returns:
        Memory text.
    """
    memory = f"**Lesson from incident:** {title}\n\n"
    memory += f"{lesson}\n\n"
    memory += f"**Source:** {source_file}\n"
    return memory


def create_negative_rule_memory(title: str,
                                 rule: str,
                                 source_file: str) -> str:
    """
    Create a memory from a negative rule.

    Args:
        title: Incident title
        rule: Negative rule statement
        source_file: Source file name

    Returns:
        Memory text.
    """
    memory = f"**IMPORTANT:** {rule}\n\n"
    memory += f"This rule comes from the incident \"{title}\". "
    memory += f"Violating this caused a production issue.\n\n"
    memory += f"**Source:** {source_file}\n"
    return memory


def import_incident(file_path: Path,
                   scope: str = "project",
                   auto_store: bool = False) -> Dict:
    """
    Import an incident postmortem as memories.

    Args:
        file_path: Path to incident file
        scope: Memory scope
        auto_store: If True, automatically store memories

    Returns:
        Import result.
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        # Extract metadata
        metadata = extract_incident_metadata(content)
        title = metadata.get("title", file_path.stem)

        result = {
            "file": str(file_path),
            "title": title,
            "severity": metadata.get("severity", "Unknown"),
            "lessons_extracted": 0,
            "rules_extracted": 0,
            "memories": [],
        }

        # Extract lessons
        lessons = extract_lessons(content)
        for lesson in lessons:
            memory_text = create_lesson_memory(title, lesson, file_path.name)
            memory_data = {
                "type": "lesson",
                "text": memory_text[:100] + "...",
            }

            if auto_store:
                try:
                    store_result = skill_remember(memory_text)
                    memory_data["stored"] = True
                except Exception as e:
                    memory_data["error"] = str(e)

            result["memories"].append(memory_data)
            result["lessons_extracted"] += 1

        # Extract negative rules
        rules = extract_negative_rules(content)
        for rule in rules:
            memory_text = create_negative_rule_memory(title, rule, file_path.name)
            memory_data = {
                "type": "negative_rule",
                "text": memory_text[:100] + "...",
            }

            if auto_store:
                try:
                    store_result = skill_remember(memory_text)
                    memory_data["stored"] = True
                except Exception as e:
                    memory_data["error"] = str(e)

            result["memories"].append(memory_data)
            result["rules_extracted"] += 1

        # Also store root cause if available
        root_cause = extract_root_cause(content)
        if root_cause:
            memory_text = f"**Root cause of incident \"{title}\":** {root_cause}\n\n**Source:** {file_path.name}"
            memory_data = {
                "type": "root_cause",
                "text": memory_text[:100] + "...",
            }

            if auto_store:
                try:
                    store_result = skill_remember(memory_text)
                    memory_data["stored"] = True
                except Exception as e:
                    memory_data["error"] = str(e)

            result["memories"].append(memory_data)

        return result

    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e)
        }


def import_all_incidents(scope: str = "project",
                         auto_store: bool = False) -> Dict:
    """
    Import all incident postmortems from the repository.

    Args:
        scope: Memory scope
        auto_store: If True, automatically store memories

    Returns:
        Import results summary.
    """
    incident_files = find_incident_files()

    if not incident_files:
        return {
            "error": "No incident files found. Checked: " + ", ".join(INCIDENT_PATHS)
        }

    results = {
        "total_found": len(incident_files),
        "processed": 0,
        "total_lessons": 0,
        "total_rules": 0,
        "files": [],
    }

    for file_path in incident_files:
        result = import_incident(file_path, scope, auto_store)
        results["files"].append(result)

        if "error" not in result:
            results["processed"] += 1
            results["total_lessons"] += result.get("lessons_extracted", 0)
            results["total_rules"] += result.get("rules_extracted", 0)

    return results


def print_results(results: Dict) -> None:
    """Print import results."""
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    print(f"\n{'='*60}")
    print("Incident Import Results")
    print(f"{'='*60}")

    if "total_found" in results:
        print(f"\nTotal incidents found: {results['total_found']}")
        print(f"Processed: {results['processed']}")
        print(f"Lessons extracted: {results['total_lessons']}")
        print(f"Negative rules: {results['total_rules']}")

        print(f"\n--- Files ---")
        for f in results["files"]:
            if "error" in f:
                print(f"[ERROR] {Path(f['file']).name}: {f['error']}")
            else:
                print(f"[OK] {f['title']}")
                print(f"     Lessons: {f.get('lessons_extracted', 0)}, "
                      f"Rules: {f.get('rules_extracted', 0)}")
    else:
        # Single file result
        if "error" in results:
            print(f"[ERROR] {Path(results['file']).name}: {results['error']}")
        else:
            print(f"[OK] {results['title']}")
            print(f"   Lessons: {results.get('lessons_extracted', 0)}, "
                  f"Rules: {results.get('rules_extracted', 0)}")
            for mem in results.get("memories", [])[:3]:
                status = "[+]" if mem.get("stored") else "[ ]"
                print(f"   {status} {mem.get('type', 'unknown')}: {mem.get('text', '')[:50]}...")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import incident postmortems"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Specific incident file to import"
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
        help="Import all incidents from repository"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if args.all:
        results = import_all_incidents(args.scope, args.store)
    elif args.file:
        results = import_incident(Path(args.file), args.scope, args.store)
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
