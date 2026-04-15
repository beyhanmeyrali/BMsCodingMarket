"""
PR Extractor for AgentBrain

Analyzes pull request review comments to extract coding conventions and patterns.
Uses gh CLI to fetch PR data, then extracts actionable patterns.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add scripts to path
plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
sys.path.insert(0, str(plugin_root / "scripts"))

from skill_remember import skill_remember


def run_gh_command(args: List[str]) -> Dict:
    """
    Run gh CLI command and return JSON output.

    Args:
        args: Command arguments (without 'gh' prefix)

    Returns:
        Parsed JSON output or empty dict on error.
    """
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_pr_reviews(pr_number: Optional[int] = None) -> List[Dict]:
    """
    Get review comments for a PR.

    Args:
        pr_number: PR number (uses current PR if None)

    Returns:
        List of review comments with metadata.
    """
    if pr_number:
        return run_gh_command([
            "pr", "view", str(pr_number),
            "--json", "reviews",
            "--jq", ".reviews[]"
        ]) or []

    # Get current PR
    pr_data = run_gh_command([
        "pr", "view",
        "--json", "number,reviews"
    ])

    if not pr_data:
        return []

    return pr_data.get("reviews", [])


def get_pr_review_comments(pr_number: Optional[int] = None) -> List[Dict]:
    """
    Get review comments for a PR.

    Args:
        pr_number: PR number (uses current PR if None)

    Returns:
        List of review comments with metadata.
    """
    if pr_number:
        return run_gh_command([
            "pr", "view", str(pr_number),
            "--json", "comments",
            "--jq", ".comments[] | select(.authorAssociation != \"NONE\")"
        ]) or []

    # Get current PR
    pr_data = run_gh_command([
        "pr", "view",
        "--json", "number,comments"
    ])

    if not pr_data:
        return []

    # Filter out non-review comments
    comments = pr_data.get("comments", [])
    return [c for c in comments if c.get("authorAssociation") != "NONE"]


def extract_patterns_from_comments(comments: List[Dict]) -> List[Dict]:
    """
    Extract coding patterns from review comments.

    Args:
        comments: List of comment dictionaries

    Returns:
        List of extracted patterns with provenance.
    """
    patterns = []

    for comment in comments:
        body = comment.get("body", "")
        author = comment.get("author", {}).get("login", "unknown")
        path = comment.get("path", "")
        commit = comment.get("commitOid", "")

        # Skip short comments
        if len(body) < 20:
            continue

        # Pattern indicators
        pattern_indicators = [
            (r"(should|must|always|never|prefer|avoid|use|don't)",
             "instruction", 0.8),
            (r"(convention|standard|pattern|practice|guideline)",
             "convention", 0.9),
            (r"(why not|instead of|better to|consider using)",
             "suggestion", 0.7),
            (r"(bug|issue|fix|error|problem)",
             "issue", 0.6),
        ]

        for pattern, p_type, weight in pattern_indicators:
            if re.search(pattern, body, re.IGNORECASE):
                patterns.append({
                    "type": p_type,
                    "weight": weight,
                    "content": body,
                    "author": author,
                    "path": path,
                    "commit": commit,
                })
                break

    return patterns


def summarize_comment(comment: str, max_length: int = 100) -> str:
    """
    Summarize a comment to a concise statement.

    Args:
        comment: Comment text
        max_length: Maximum length of summary

    Returns:
        Summarized comment.
    """
    # Remove quotes, clean up
    comment = comment.strip().strip('"\'')
    comment = re.sub(r'^\s*>\s*', "", comment)  # Remove quote markers

    # Find first sentence
    match = re.match(r'^[^.!?]+[.!?]', comment)
    if match:
        summary = match.group(0).strip()
    else:
        # Take first 100 chars
        summary = comment[:max_length].split()[:-1]
        summary = " ".join(summary)

    return summary


def create_memory_text(pattern: Dict, pr_number: int) -> str:
    """
    Create a memory text from an extracted pattern.

    Args:
        pattern: Pattern dictionary
        pr_number: PR number for provenance

    Returns:
        Memory text for storage.
    """
    content = pattern["content"]
    p_type = pattern["type"]
    author = pattern["author"]
    path = pattern.get("path", "")
    provenance = f"PR #{pr_number}" if pr_number else "code review"

    # Summarize
    summary = summarize_comment(content)

    # Build memory text
    if p_type == "instruction":
        memory = f"Code review instruction from {author}: {summary}"
    elif p_type == "convention":
        memory = f"Team convention from {author} ({provenance}): {summary}"
    elif p_type == "suggestion":
        memory = f"Better practice from {author}: {summary}"
    else:  # issue
        memory = f"Issue noted by {author} ({provenance}): {summary}"

    # Add context if available
    if path:
        memory += f"\n\nContext: File {path}"

    return memory


def extract_from_pr(pr_number: Optional[int] = None,
                    auto_store: bool = False) -> Dict:
    """
    Extract patterns from a PR.

    Args:
        pr_number: PR number (uses current PR if None)
        auto_store: If True, automatically store as memories

    Returns:
        Extraction results with patterns.
    """
    # Get PR info
    if pr_number:
        pr_data = run_gh_command([
            "pr", "view", str(pr_number),
            "--json", "number,title,state,author"
        ])
    else:
        pr_data = run_gh_command([
            "pr", "view",
            "--json", "number,title,state,author"
        ])

    if not pr_data:
        return {
            "error": "Could not fetch PR data. Is gh CLI installed?"
        }

    pr_num = pr_data.get("number")
    pr_title = pr_data.get("title", "")
    pr_author = pr_data.get("author", {}).get("login", "unknown")

    # Get comments
    comments = get_pr_review_comments(pr_number)

    # Extract patterns
    patterns = extract_patterns_from_comments(comments)

    # Build results
    results = {
        "pr_number": pr_num,
        "pr_title": pr_title,
        "pr_author": pr_author,
        "patterns_found": len(patterns),
        "patterns": [],
    }

    # Process patterns
    for pattern in patterns:
        memory_text = create_memory_text(pattern, pr_num)

        pattern_data = {
            "type": pattern["type"],
            "weight": pattern["weight"],
            "author": pattern["author"],
            "memory_text": memory_text,
        }

        if auto_store:
            try:
                result = skill_remember(memory_text)
                pattern_data["stored"] = True
                pattern_data["store_result"] = result[:100]
            except Exception as e:
                pattern_data["stored"] = False
                pattern_data["error"] = str(e)

        results["patterns"].append(pattern_data)

    return results


def print_results(results: Dict) -> None:
    """Print extraction results."""
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    pr = f"#{results['pr_number']}"
    title = results['pr_title']
    count = results['patterns_found']

    print(f"\n{'='*60}")
    print(f"PR Extractor Results")
    print(f"{'='*60}")
    print(f"\nPR: {pr} - {title}")
    print(f"Author: {results['pr_author']}")
    print(f"Patterns found: {count}")

    if count == 0:
        print("\nNo actionable patterns found.")
        return

    print(f"\n--- Patterns ---")

    for i, p in enumerate(results['patterns'], 1):
        print(f"\n{i}. [{p['type'].upper()}] (by {p['author']})")
        print(f"   Weight: {p['weight']}")
        print(f"   Memory: {p['memory_text'][:100]}...")

        if p.get('stored'):
            print(f"   [STORED] {p.get('store_result', '')}")
        elif 'error' in p:
            print(f"   [ERROR] {p['error']}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract coding patterns from PR reviews"
    )
    parser.add_argument(
        "pr_number",
        nargs="?",
        type=int,
        help="PR number (defaults to current PR)"
    )
    parser.add_argument(
        "--store",
        action="store_true",
        help="Automatically store patterns as memories"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    results = extract_from_pr(
        pr_number=args.pr_number,
        auto_store=args.store
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
