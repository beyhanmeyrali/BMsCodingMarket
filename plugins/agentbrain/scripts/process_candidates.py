"""
Candidates Processing Utility

Handles the JSON-based candidates pipeline for memory curation.
Provides utilities for reading, validating, and processing curator output.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class MemoryCandidate:
    """A candidate memory from the curator."""

    action: str  # create, update, skip
    file: str
    memory_type: str  # user, feedback, project, reference
    scope: str
    frontmatter: Dict
    content: str
    reason: Optional[str] = None  # For skip actions

    def validate(self) -> bool:
        """
        Validate the candidate has required fields.

        Returns:
            True if valid, False otherwise.
        """
        if self.action not in ("create", "update", "skip"):
            return False

        if not self.file:
            return False

        if self.action in ("create", "update"):
            if self.memory_type not in ("user", "feedback", "project", "reference"):
                return False
            if not self.scope:
                return False
            if not self.content:
                return False

        return True


class CandidatesPipeline:
    """
    Manages the candidates pipeline from curator to storage.

    Pipeline stages:
    1. Curator writes JSON output
    2. Pipeline validates JSON
    3. Pipeline processes each candidate
    4. Pipeline writes memory files
    5. Pipeline triggers Qdrant sync
    """

    def __init__(self, plugin_root: Optional[Path] = None):
        """
        Initialize the pipeline.

        Args:
            plugin_root: Plugin root directory
        """
        if plugin_root is None:
            plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))

        self.plugin_root = plugin_root
        self.curator_dir = plugin_root / ".agentbrain"
        self.output_file = self.curator_dir / "curator_output.json"

    def has_output(self) -> bool:
        """Check if curator has produced output."""
        return self.output_file.exists()

    def load_output(self) -> Dict:
        """
        Load curator output JSON.

        Returns:
            Parsed JSON or empty dict on error.
        """
        if not self.has_output():
            return {}

        try:
            content = self.output_file.read_text(encoding="utf-8")
            return json.loads(content)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def parse_candidates(self, output: Dict) -> List[MemoryCandidate]:
        """
        Parse candidates from curator output.

        Args:
            output: Parsed curator JSON

        Returns:
            List of MemoryCandidate objects.
        """
        candidates = []

        for item in output.get("memories", []):
            try:
                candidate = MemoryCandidate(
                    action=item.get("action", "skip"),
                    file=item.get("file", ""),
                    memory_type=item.get("type", "other"),
                    scope=item.get("scope", ""),
                    frontmatter=item.get("frontmatter", {}),
                    content=item.get("content", ""),
                    reason=item.get("reason"),
                )
                candidates.append(candidate)
            except Exception:
                continue

        return candidates

    def validate_candidates(self, candidates: List[MemoryCandidate]) -> List[MemoryCandidate]:
        """
        Validate candidates and return only valid ones.

        Args:
            candidates: List of candidates to validate

        Returns:
            List of valid candidates.
        """
        return [c for c in candidates if c.validate()]

    def get_stats(self, candidates: List[MemoryCandidate]) -> Dict:
        """
        Get statistics about candidates.

        Args:
            candidates: List of candidates

        Returns:
            Statistics dict.
        """
        stats = {
            "total": len(candidates),
            "create": sum(1 for c in candidates if c.action == "create"),
            "update": sum(1 for c in candidates if c.action == "update"),
            "skip": sum(1 for c in candidates if c.action == "skip"),
            "by_type": {
                "user": sum(1 for c in candidates if c.memory_type == "user"),
                "feedback": sum(1 for c in candidates if c.memory_type == "feedback"),
                "project": sum(1 for c in candidates if c.memory_type == "project"),
                "reference": sum(1 for c in candidates if c.memory_type == "reference"),
            },
        }

        return stats

    def cleanup(self) -> None:
        """Clean up temporary curator files."""
        if not self.curator_dir.exists():
            return

        for file in self.curator_dir.glob("curator_*"):
            try:
                file.unlink()
            except Exception:
                pass

        marker = self.curator_dir / "curation_needed.txt"
        try:
            if marker.exists():
                marker.unlink()
        except Exception:
            pass


def main():
    """CLI for testing the candidates pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="AgentBrain candidates pipeline")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--validate", action="store_true", help="Validate candidates")
    parser.add_argument("--cleanup", action="store_true", help="Clean up temporary files")

    args = parser.parse_args()

    pipeline = CandidatesPipeline()

    if args.cleanup:
        pipeline.cleanup()
        print("Cleaned up temporary files")
        return

    if not pipeline.has_output():
        print("No curator output found")
        return

    output = pipeline.load_output()
    if "error" in output:
        print(f"Error loading output: {output['error']}")
        return

    candidates = pipeline.parse_candidates(output)
    valid_candidates = pipeline.validate_candidates(candidates)

    print(f"Total candidates: {len(candidates)}")
    print(f"Valid candidates: {len(valid_candidates)}")

    if args.stats:
        stats = pipeline.get_stats(valid_candidates)
        print(f"\nStatistics:")
        print(f"  Create: {stats['create']}")
        print(f"  Update: {stats['update']}")
        print(f"  Skip: {stats['skip']}")
        print(f"\nBy type:")
        for memory_type, count in stats["by_type"].items():
            if count:
                print(f"  {memory_type}: {count}")

    if args.validate:
        print("\nValid candidates:")
        for c in valid_candidates:
            print(f"  [{c.action}] {c.file} ({c.memory_type}, {c.scope})")

        invalid = [c for c in candidates if c not in valid_candidates]
        if invalid:
            print(f"\nInvalid candidates: {len(invalid)}")
            for c in invalid:
                print(f"  [{c.action}] {c.file}")


if __name__ == "__main__":
    main()
