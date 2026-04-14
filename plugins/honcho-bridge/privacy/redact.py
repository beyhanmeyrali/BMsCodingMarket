#!/usr/bin/env python3
"""
Privacy redaction module for Honcho memory.

Detects and redacts sensitive information before storage.
"""

import re
import os
from typing import Dict, List, Tuple, Optional


# Default redaction patterns
DEFAULT_PATTERNS: Dict[str, str] = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "api_key": r"\b(API_?KEY|SECRET|TOKEN|API_KEY)\s*[:=]\s*\S+",
    "password": r"\b(PASSWORD|PASS|PWD|PASSWORD)\s*[:=]\s*\S+",
    "ip": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "aws_key": r"\b(AKIA[0-9A-Z]{16})\b",
    "github_token": r"\b(ghp_[a-zA-Z0-9]{36})\b",
    "slack_token": r"\b(xox[pbar]-[a-zA-Z0-9-]{10,})\b",
    "jwt": r"\b(eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)\b",
    "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    "credit_card": r"\b(\d{4}[-\s]?){3}\d{4}\b",
}

# Replacement patterns
REPLACEMENTS: Dict[str, str] = {
    "email": "***@***.***",
    "api_key": "***REDACTED_API_KEY***",
    "password": "***REDACTED_PASSWORD***",
    "ip": "***.***.***.***",
    "aws_key": "AKIA********************",
    "github_token": "ghp_************************************",
    "slack_token": "xoxb-********************",
    "jwt": "eyJ***.***.*****",
    "uuid": "****-****-****-****-************",
    "credit_card": "****-****-****-****",
}


def load_env_config() -> Dict[str, str]:
    """Load configuration from .env file in current directory."""
    config = {}
    env_file = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def get_enabled_patterns() -> List[str]:
    """Get list of enabled redaction patterns from env."""
    config = load_env_config()
    patterns_str = config.get("HONCHO_REDACT_PATTERNS", "email,api_key,password,ip")
    return [p.strip() for p in patterns_str.split(",") if p.strip()]


def is_privacy_enabled() -> bool:
    """Check if privacy redaction is enabled."""
    config = load_env_config()
    return config.get("HONCHO_PRIVACY_ENABLED", "true").lower() == "true"


def redact(text: str, patterns: Optional[Dict[str, str]] = None) -> Tuple[str, List[Dict]]:
    """
    Redact sensitive information from text.

    Args:
        text: The text to redact
        patterns: Optional custom patterns dict {name: regex}

    Returns:
        Tuple of (redacted_text, list of detected secrets)
        Each secret dict has: {type, original, redacted, position}
    """
    if not is_privacy_enabled():
        return text, []

    if patterns is None:
        patterns = DEFAULT_PATTERNS

    redacted_text = text
    detected: List[Dict] = []
    enabled = get_enabled_patterns()

    # Process in reverse order to preserve positions
    all_matches = []

    for pattern_name in enabled:
        if pattern_name not in patterns:
            continue
        pattern = patterns[pattern_name]
        replacement = REPLACEMENTS.get(pattern_name, f"***REDACTED_{pattern_name.upper()}***")

        for match in re.finditer(pattern, text, re.IGNORECASE):
            all_matches.append({
                "start": match.start(),
                "end": match.end(),
                "original": match.group(0),
                "redacted": replacement,
                "type": pattern_name,
            })

    # Sort by position (descending) to replace from end
    all_matches.sort(key=lambda x: x["start"], reverse=True)

    # Apply replacements
    for match in all_matches:
        start, end = match["start"], match["end"]
        redacted_text = redacted_text[:start] + match["redacted"] + redacted_text[end:]
        detected.append(match)

    return redacted_text, detected


def should_store_path(file_path: str, ignore_patterns: Optional[List[str]] = None) -> bool:
    """
    Check if a file path should be stored or ignored.

    Args:
        file_path: The file path to check
        ignore_patterns: Optional list of glob patterns to ignore

    Returns:
        True if file should be stored, False if ignored
    """
    if ignore_patterns is None:
        # Default ignore patterns
        ignore_patterns = [
            "*.key",
            "*.pem",
            "*.cert",
            "*.secrets",
            ".env.local",
            ".env.secrets",
            "id_rsa",
            "id_ed25519",
        ]

    from fnmatch import fnmatch

    # Check basename and full path
    for pattern in ignore_patterns:
        if fnmatch(os.path.basename(file_path), pattern) or fnmatch(file_path, pattern):
            return False

    return True


def detect_secrets(text: str) -> List[Dict]:
    """
    Detect potential secrets in text without redacting.

    Returns:
        List of detected secrets with metadata
    """
    _, detected = redact(text)
    return detected


class PrivacyFilter:
    """Privacy filter for message processing."""

    def __init__(self, enabled: Optional[bool] = None, patterns: Optional[List[str]] = None):
        """
        Initialize privacy filter.

        Args:
            enabled: Override privacy enabled setting
            patterns: Override enabled patterns list
        """
        self._enabled = enabled if enabled is not None else is_privacy_enabled()
        self._patterns = patterns if patterns is not None else get_enabled_patterns()

    def filter_message(self, content: str, metadata: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Filter a message content and metadata.

        Args:
            content: The message content
            metadata: Optional metadata dict to also filter

        Returns:
            Tuple of (filtered_content, filtered_metadata)
        """
        filtered_content, secrets = redact(content)

        filtered_metadata = metadata or {}
        if filtered_metadata:
            # Filter string values in metadata
            for key, value in filtered_metadata.items():
                if isinstance(value, str):
                    filtered_metadata[key], _ = redact(value)

        return filtered_content, filtered_metadata

    def should_ignore(self, file_path: str) -> bool:
        """Check if a file path should be ignored."""
        return not should_store_path(file_path)


# CLI for testing
def main():
    """Test redaction functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Test privacy redaction")
    parser.add_argument("text", nargs="?", help="Text to redact")
    parser.add_argument("--file", "-f", help="Read text from file")
    parser.add_argument("--patterns", "-p", help="Comma-separated patterns to enable")
    parser.add_argument("--detect", "-d", action="store_true", help="Only detect, don't redact")

    args = parser.parse_args()

    # Override patterns if specified
    if args.patterns:
        os.environ["HONCHO_REDACT_PATTERNS"] = args.patterns

    # Get text
    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        text = """Here are some secrets:
API_KEY=sk-1234567890abcdef
email: user@example.com
password: secret123
IP: 192.168.1.1
AWS: AKIAIOSFODNN7EXAMPLE
GitHub: ghp_githubTokenExample1234567890abcdef
"""

    if args.detect:
        secrets = detect_secrets(text)
        print(f"Detected {len(secrets)} potential secrets:")
        for secret in secrets:
            print(f"  - {secret['type']}: {secret['original'][:50]}")
    else:
        redacted, secrets = redact(text)
        print("Redacted text:")
        print(redacted)
        print(f"\nRedacted {len(secrets)} items")


if __name__ == "__main__":
    main()
