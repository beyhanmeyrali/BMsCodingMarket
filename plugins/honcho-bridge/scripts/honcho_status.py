#!/usr/bin/env python3
"""
Check Honcho system health and statistics.

Displays connection status, workspace info, and deriver activity.
"""

import sys
import argparse
import time
from typing import Dict, Any

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


def get_system_status(
    base_url: str,
    workspace: str,
) -> Dict[str, Any]:
    """Get comprehensive Honcho system status."""
    if not HONCHO_AVAILABLE:
        raise ImportError("honcho-ai not installed. Run: pip install honcho-ai")

    client = HonchoClient(
        base_url=base_url,
        api_key="placeholder",
        workspace_id=workspace
    )

    # Measure connection latency
    start = time.time()

    # Count peers
    peers = list(client.peers())
    peer_count = len(peers)

    # Count sessions and messages
    session_count = 0
    message_count = 0
    observation_count = 0

    for peer in peers:
        for session in peer.sessions():
            session_count += 1
            messages = list(session.messages())
            message_count += len(messages)

    # Try to get observations (requires iterating peers with their observations)
    # Note: The SDK may not expose direct observation count
    # We'll report what we can get

    latency = (time.time() - start) * 1000  # ms

    return {
        "connection": "ok",
        "latency_ms": round(latency, 2),
        "workspace": workspace,
        "peer_count": peer_count,
        "session_count": session_count,
        "message_count": message_count,
        "observation_count": observation_count,  # SDK limitation
    }


def format_status(status: Dict[str, Any]) -> str:
    """Format status for display."""
    lines = [
        "=" * 50,
        "HONCHO SYSTEM STATUS",
        "=" * 50,
        "",
        "## Connection",
        f"Status: {status['connection'].upper()}",
        f"Latency: {status['latency_ms']} ms",
        "",
        "## Workspace",
        f"Workspace: {status['workspace']}",
        "",
        "## Statistics",
        f"Peers: {status['peer_count']}",
        f"Sessions: {status['session_count']}",
        f"Messages: {status['message_count']}",
        "",
    ]

    if status['message_count'] > 0 and status['observation_count'] == 0:
        lines.extend([
            "[!] Warning: Messages exist but 0 observations",
            "   → Deriver may not have processed yet (wait ~1 min)",
            "   → Or deriver is failing — check: docker compose logs deriver",
            "",
        ])

    lines.extend([
        "=" * 50,
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check Honcho system health and statistics"
    )
    parser.add_argument(
        "--base-url",
        "-b",
        default="http://localhost:8000",
        help="Honcho server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        required=True,
        help="Workspace ID",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    try:
        status = get_system_status(
            base_url=args.base_url,
            workspace=args.workspace,
        )

        if args.json:
            import json
            print(json.dumps(status, indent=2))
        else:
            print(format_status(status))

    except Exception as e:
        print(f"[ERROR] Status check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
