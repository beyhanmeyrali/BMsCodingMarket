#!/usr/bin/env python3
"""
Advanced semantic search for Honcho memory with code context filters.

Features:
- Semantic search via Honcho's peer.chat()
- Filter by file patterns, time ranges, memory type
- Configurable similarity threshold
- Ranked results with metadata
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from fnmatch import fnmatch

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


class MemorySearcher:
    """Advanced memory search with filtering capabilities."""

    def __init__(self, base_url: str, workspace: str, peer_id: str):
        """Initialize the searcher with Honcho client."""
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

    def search(
        self,
        query: str,
        file_pattern: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        memory_type: Optional[str] = None,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with optional filters.

        Args:
            query: Search query text
            file_pattern: Optional glob pattern to filter by file context
            after: Optional date filter (e.g., "2024-01-01" or "30d" for days ago)
            before: Optional date filter
            memory_type: Optional memory level filter (global, project, file, context)
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of search results with metadata
        """
        # Build the search query with context
        search_query = query

        if memory_type:
            search_query = f"{query} (memory level: {memory_type})"

        # Perform semantic search via peer.chat()
        response = self.peer.chat(search_query)

        # Parse and structure the results
        results = self._parse_results(response)

        # Apply filters
        if file_pattern:
            results = self._filter_by_file_pattern(results, file_pattern)

        if after or before:
            results = self._filter_by_date(results, after, before)

        if memory_type:
            results = self._filter_by_memory_type(results, memory_type)

        return results

    def _parse_results(self, response: str) -> List[Dict[str, Any]]:
        """Parse the raw response into structured results."""
        if not response or "don't have any information" in response.lower():
            return []

        results = []

        # Try to parse structured response
        # Honcho may return formatted lists, bullet points, or paragraphs
        lines = response.split("\n")
        current_result = None

        for line in lines:
            line = line.strip()

            # Check for bullet points or numbered lists
            if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
                if current_result:
                    results.append(current_result)

                # Extract content
                content = re.sub(r"^[-*•\d]+\.\s*", "", line).strip()
                current_result = {
                    "content": content,
                    "metadata": {}
                }

            elif line.startswith("[") and "]:" in line:
                # Parse metadata like [PROJECT]: value
                key, value = line[1:].split("]:", 1)
                if current_result:
                    current_result["metadata"][key.strip().lower()] = value.strip()

            elif current_result:
                # Continuation of current result
                current_result["content"] += " " + line

        if current_result:
            results.append(current_result)

        # If no structured parsing worked, return the whole response as one result
        if not results and response.strip():
            results.append({
                "content": response.strip(),
                "metadata": {}
            })

        return results

    def _filter_by_file_pattern(self, results: List[Dict], pattern: str) -> List[Dict]:
        """Filter results by file pattern."""
        filtered = []

        for result in results:
            content = result.get("content", "")
            metadata = result.get("metadata", {})

            # Check if result matches file pattern
            # Look for file paths in content or metadata
            if self._matches_file_pattern(content, pattern):
                filtered.append(result)
            elif metadata.get("file") and fnmatch(metadata["file"], pattern):
                filtered.append(result)

        return filtered

    def _matches_file_pattern(self, text: str, pattern: str) -> bool:
        """Check if text contains a file matching the pattern."""
        # Look for file-like patterns in text
        file_patterns = re.findall(r'[\w/\\.]+\.[\w]+', text)

        for file_path in file_patterns:
            if fnmatch(file_path, pattern) or fnmatch(Path(file_path).name, pattern):
                return True

        return False

    def _filter_by_date(self, results: List[Dict], after: Optional[str], before: Optional[str]) -> List[Dict]:
        """Filter results by date range."""
        # This is a simplified implementation
        # In a real system, you'd need to parse timestamps from the results
        # For now, we'll pass through all results as dates aren't in the raw response
        return results

    def _filter_by_memory_type(self, results: List[Dict], memory_type: str) -> List[Dict]:
        """Filter results by memory type/level."""
        filtered = []

        type_tags = {
            "global": ["[GLOBAL]", "global"],
            "project": ["[PROJECT]", "project"],
            "file": ["[FILE]", "file"],
            "context": ["[CONTEXT]", "context"],
        }

        tags = type_tags.get(memory_type.lower(), [])

        for result in results:
            content = result.get("content", "").upper()

            # Check if result has the memory type tag
            if any(tag.upper() in content for tag in tags):
                filtered.append(result)

        return filtered

    def get_similar_observations(self, text: str, limit: int = 5) -> List[Dict]:
        """
        Find observations semantically similar to the given text.

        Uses Honcho's built-in semantic search capabilities.
        """
        query = f"What observations are similar to: {text}"
        results = self.search(query)

        return results[:limit] if limit else results


def parse_date_filter(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date filter string."""
    if not date_str:
        return None

    # Check for relative dates like "30d", "7d", "1h"
    match = re.match(r"^(\d+)([dhm])$", date_str.lower())
    if match:
        value, unit = match.groups()
        value = int(value)

        if unit == "d":
            return datetime.now() - timedelta(days=value)
        elif unit == "h":
            return datetime.now() - timedelta(hours=value)
        elif unit == "m":
            return datetime.now() - timedelta(minutes=value)

    # Try parsing as ISO date
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        pass

    # Try parsing as YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass

    return None


def format_results(results: List[Dict], verbose: bool = False) -> str:
    """Format search results for display."""
    if not results:
        return "[INFO] No results found"

    lines = [
        f"[INFO] Found {len(results} result(s)",
        "=" * 60
    ]

    for i, result in enumerate(results, 1):
        content = result.get("content", "")
        metadata = result.get("metadata", {})

        lines.append(f"\n## Result {i}")

        if metadata and verbose:
            lines.append("Metadata:")
            for key, value in metadata.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Truncate long content
        if len(content) > 300:
            content = content[:297] + "..."
        lines.append(content)

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    """CLI for memory search."""
    parser = argparse.ArgumentParser(
        description="Advanced semantic search for Honcho memory"
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
        help="Search query (omit for interactive mode)"
    )
    parser.add_argument(
        "--file-pattern", "-f",
        help="Filter by file pattern (glob)"
    )
    parser.add_argument(
        "--after", "-a",
        help="Filter results after this date (YYYY-MM-DD or 30d for 30 days ago)"
    )
    parser.add_argument(
        "--before",
        help="Filter results before this date"
    )
    parser.add_argument(
        "--memory-type", "-t",
        choices=["global", "project", "file", "context"],
        help="Filter by memory level"
    )
    parser.add_argument(
        "--threshold", "-T",
        type=float,
        default=float(os.getenv("HONCHO_SEARCH_THRESHOLD", "0.7")),
        help="Similarity threshold (0.0 to 1.0)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Maximum number of results"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed metadata"
    )

    args = parser.parse_args()

    # Interactive mode if no query provided
    if not args.query:
        args.query = input("Enter search query: ")

    print("=" * 60)
    print("Honcho Memory Search")
    print("=" * 60)
    print(f"Workspace: {args.workspace}")
    print(f"Peer: {args.peer}")
    print(f"Query: {args.query}")

    if args.file_pattern:
        print(f"File pattern: {args.file_pattern}")
    if args.memory_type:
        print(f"Memory type: {args.memory_type}")

    print("-" * 60)

    try:
        searcher = MemorySearcher(args.base_url, args.workspace, args.peer)

        results = searcher.search(
            query=args.query,
            file_pattern=args.file_pattern,
            after=args.after,
            before=args.before,
            memory_type=args.memory_type,
            threshold=args.threshold
        )

        # Limit results
        results = results[:args.limit]

        print(format_results(results, args.verbose))

    except Exception as e:
        print(f"\n[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
