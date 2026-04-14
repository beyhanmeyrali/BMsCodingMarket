#!/usr/bin/env python3
"""
Memory health dashboard for Honcho.

Monitors:
- Stale observations (never queried in X days)
- Deriver lag (unprocessed messages)
- Storage trends
- Duplicate/conflicting observations
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

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


class MemoryHealthChecker:
    """Comprehensive health checker for Honcho memory."""

    def __init__(self, base_url: str, workspace: str, peer_id: str):
        """Initialize the health checker."""
        if not HONCHO_AVAILABLE:
            raise ImportError("honcho-ai not installed")

        self.client = HonchoClient(
            base_url=base_url,
            api_key="placeholder",
            workspace_id=workspace
        )
        self.workspace = workspace
        self.peer_id = peer_id
        self.peer = self.client.peer(peer_id)

    def check_freshness(self, stale_threshold_days: int = 30) -> Dict[str, Any]:
        """
        Find observations that haven't been queried recently.

        Returns stats about stale observations.
        """
        try:
            # Get all sessions for this peer
            sessions = list(self.peer.sessions())

            now = datetime.now()
            stale_threshold = timedelta(days=stale_threshold_days)

            stale_sessions = []
            total_messages = 0
            stale_messages = 0

            for session in sessions:
                messages = list(session.messages())
                total_messages += len(messages)

                # Check session age
                if session.created_at:
                    try:
                        if hasattr(session.created_at, "astimezone"):
                            created = session.created_at.astimezone()
                        else:
                            created = session.created_at

                        age = now - created
                        if age > stale_threshold:
                            stale_sessions.append({
                                "session_id": session.id,
                                "age_days": age.days,
                                "message_count": len(messages)
                            })
                            stale_messages += len(messages)
                    except Exception:
                        pass

            return {
                "total_sessions": len(sessions),
                "total_messages": total_messages,
                "stale_sessions": len(stale_sessions),
                "stale_messages": stale_messages,
                "stale_threshold_days": stale_threshold_days,
                "stale_details": stale_sessions[:10]  # First 10
            }

        except Exception as e:
            return {
                "error": str(e),
                "total_sessions": 0,
                "total_messages": 0,
                "stale_sessions": 0,
                "stale_messages": 0
            }

    def check_deriver_lag(self, warning_minutes: int = 5) -> Dict[str, Any]:
        """
        Detect messages that haven't been processed by the deriver.

        The deriver runs periodically (usually every minute) to extract
        observations from raw messages. This checks for lag.
        """
        try:
            # Get recent sessions and check message ages
            now = datetime.now()
            warning_threshold = timedelta(minutes=warning_minutes)

            recent_sessions = []
            unprocessed_count = 0
            total_recent = 0

            for session in self.peer.sessions():
                messages = list(session.messages())

                for msg in messages:
                    if msg.created_at:
                        try:
                            if hasattr(msg.created_at, "astimezone"):
                                created = msg.created_at.astimezone()
                            else:
                                created = msg.created_at

                            age = now - created
                            if age < timedelta(hours=1):  # Recent messages
                                total_recent += 1
                                if age > warning_threshold:
                                    unprocessed_count += 1
                                    recent_sessions.append({
                                        "session_id": session.id,
                                        "age_minutes": int(age.total_seconds() / 60),
                                        "content_preview": msg.content[:50]
                                    })
                        except Exception:
                            pass

            # Determine if deriver is lagging
            lag_warning = unprocessed_count > 0

            return {
                "total_recent_messages": total_recent,
                "unprocessed_count": unprocessed_count,
                "lag_warning": lag_warning,
                "warning_threshold_minutes": warning_minutes,
                "unprocessed_details": recent_sessions[:10]
            }

        except Exception as e:
            return {
                "error": str(e),
                "total_recent_messages": 0,
                "unprocessed_count": 0,
                "lag_warning": False
            }

    def check_storage_trends(self) -> Dict[str, Any]:
        """
        Analyze storage growth trends over time.

        Returns statistics about how memory usage is growing.
        """
        try:
            sessions = list(self.peer.sessions())

            if not sessions:
                return {
                    "total_sessions": 0,
                    "total_messages": 0,
                    "avg_messages_per_session": 0,
                    "growth_trend": "no_data"
                }

            # Group sessions by date
            daily_counts = {}
            total_messages = 0

            for session in sessions:
                messages = list(session.messages())
                total_messages += len(messages)

                if session.created_at:
                    try:
                        if hasattr(session.created_at, "date"):
                            date_key = session.created_at.date()
                        else:
                            date_key = datetime.fromisoformat(str(session.created_at).replace("Z", "+00:00")).date()

                        daily_counts[date_key] = daily_counts.get(date_key, 0) + len(messages)
                    except Exception:
                        pass

            # Calculate trend
            sorted_dates = sorted(daily_counts.keys())
            if len(sorted_dates) >= 2:
                recent_avg = sum(daily_counts.get(d, 0) for d in sorted_dates[-7:]) / min(7, len(sorted_dates))
                older_avg = sum(daily_counts.get(d, 0) for d in sorted_dates[:-7]) / max(1, len(sorted_dates) - 7)

                if recent_avg > older_avg * 1.5:
                    trend = "growing"
                elif recent_avg < older_avg * 0.5:
                    trend = "shrinking"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            return {
                "total_sessions": len(sessions),
                "total_messages": total_messages,
                "avg_messages_per_session": total_messages / len(sessions) if sessions else 0,
                "days_with_activity": len(daily_counts),
                "growth_trend": trend,
                "daily_breakdown": dict(list(daily_counts.items())[-30:])  # Last 30 days
            }

        except Exception as e:
            return {
                "error": str(e),
                "total_sessions": 0,
                "total_messages": 0,
                "growth_trend": "unknown"
            }

    def detect_duplicates(self) -> Dict[str, Any]:
        """
        Detect potentially duplicate or conflicting observations.

        Uses semantic similarity to find similar observations.
        """
        try:
            # Get recent observations via chat
            response = self.peer.chat(
                "What are the most recent observations? List them briefly."
            )

            if not response or "don't have any information" in response.lower():
                return {
                    "potential_duplicates": 0,
                    "details": []
                }

            # Simple duplicate detection based on content similarity
            # In production, you'd use embedding similarity
            lines = response.split("\n")
            seen = {}
            duplicates = []

            for line in lines:
                line = line.strip()
                if len(line) < 20:  # Skip short lines
                    continue

                # Normalize for comparison
                normalized = line.lower().replace(".", "").replace(",", "").strip()

                # Check for similar content
                for seen_norm, seen_line in seen.items():
                    # Simple similarity check
                    if normalized in seen_norm or seen_norm in normalized:
                        duplicates.append({
                            "original": seen_line,
                            "similar": line
                        })
                        break

                seen[normalized] = line

            return {
                "potential_duplicates": len(duplicates),
                "details": duplicates[:5]  # First 5
            }

        except Exception as e:
            return {
                "error": str(e),
                "potential_duplicates": 0
            }

    def generate_report(self, stale_threshold: int = 30, deriver_threshold: int = 5) -> Dict[str, Any]:
        """
        Generate a comprehensive health report.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "workspace": self.workspace,
            "peer_id": self.peer_id,
            "freshness": self.check_freshness(stale_threshold),
            "deriver": self.check_deriver_lag(deriver_threshold),
            "storage": self.check_storage_trends(),
            "duplicates": self.detect_duplicates()
        }


def format_health_report(report: Dict[str, Any]) -> str:
    """Format health report for display."""
    lines = [
        "=" * 60,
        "HONCHO MEMORY HEALTH REPORT",
        "=" * 60,
        f"Workspace: {report['workspace']}",
        f"Peer: {report['peer_id']}",
        f"Timestamp: {report['timestamp']}",
        ""
    ]

    # Freshness section
    freshness = report.get("freshness", {})
    lines.extend([
        "## Observation Freshness",
        f"Total Messages: {freshness.get('total_messages', 0)}",
        f"Stale Messages: {freshness.get('stale_messages', 0)} (older than {freshness.get('stale_threshold_days', 30)} days)",
    ])

    if freshness.get("stale_messages", 0) > 0:
        lines.append("  ⚠️  Some observations may be outdated")

    lines.append("")

    # Deriver section
    deriver = report.get("deriver", {})
    lines.extend([
        "## Deriver Status",
        f"Recent Messages: {deriver.get('total_recent_messages', 0)}",
        f"Unprocessed: {deriver.get('unprocessed_count', 0)}",
    ])

    if deriver.get("lag_warning"):
        lines.append(f"  ⚠️  Deriver may be lagging (> {deriver.get('warning_threshold_minutes', 5)} minutes)")
    else:
        lines.append("  ✅ Deriver processing normally")

    lines.append("")

    # Storage section
    storage = report.get("storage", {})
    trend = storage.get("growth_trend", "unknown")
    trend_emoji = {
        "growing": "📈",
        "shrinking": "📉",
        "stable": "➡️",
        "unknown": "❓"
    }.get(trend, "❓")

    lines.extend([
        "## Storage Trends",
        f"Total Sessions: {storage.get('total_sessions', 0)}",
        f"Total Messages: {storage.get('total_messages', 0)}",
        f"Growth Trend: {trend_emoji} {trend}",
        ""
    ])

    # Duplicates section
    dupes = report.get("duplicates", {})
    dup_count = dupes.get("potential_duplicates", 0)

    lines.extend([
        "## Duplicate Detection",
        f"Potential Duplicates: {dup_count}",
    ])

    if dup_count > 0:
        lines.append("  ⚠️  Some observations may be redundant")
        for detail in dupes.get("details", [])[:3]:
            lines.append(f"  - {detail.get('similar', '')[:50]}")

    lines.extend([
        "",
        "=" * 60
    ])

    return "\n".join(lines)


def main():
    """CLI for memory health checking."""
    parser = argparse.ArgumentParser(
        description="Check Honcho memory health"
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
        "--stale-threshold",
        type=int,
        default=int(os.getenv("HONCHO_STALE_THRESHOLD_DAYS", "30")),
        help="Days before considering observations stale"
    )
    parser.add_argument(
        "--deriver-threshold",
        type=int,
        default=int(os.getenv("HONCHO_DERIVER_LAG_WARNING_MINUTES", "5")),
        help="Minutes before warning about deriver lag"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    try:
        checker = MemoryHealthChecker(
            args.base_url,
            args.workspace,
            args.peer
        )

        report = checker.generate_report(
            stale_threshold=args.stale_threshold,
            deriver_threshold=args.deriver_threshold
        )

        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print(format_health_report(report))

    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
