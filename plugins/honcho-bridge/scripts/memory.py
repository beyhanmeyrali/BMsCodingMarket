#!/usr/bin/env python3
"""
Honcho memory interface for BMsCodingMarket.

Provides a thin, project-scoped wrapper around the official Honcho SDK
using the local Docker stack.
"""

from __future__ import annotations

from typing import Optional

from honcho import Honcho, Peer, Session

HONCHO_BASE_URL = "http://localhost:8000"
HONCHO_API_KEY = "placeholder"
DEFAULT_WORKSPACE = "bms-coding-market"


class ProjectMemory:
    """
    Project-scoped Honcho memory client.

    Uses get-or-create semantics for workspace, peers, and sessions —
    safe to instantiate repeatedly with the same IDs.
    """

    def __init__(
        self,
        workspace_id: str = DEFAULT_WORKSPACE,
        base_url: str = HONCHO_BASE_URL,
    ) -> None:
        self._client = Honcho(
            base_url=base_url,
            api_key=HONCHO_API_KEY,
            workspace_id=workspace_id,
        )

    def peer(self, peer_id: str, **metadata) -> Peer:
        return self._client.peer(peer_id, metadata=metadata or None)

    def session(self, session_id: str, **metadata) -> Session:
        return self._client.session(session_id, metadata=metadata or None)

    def remember(self, peer_id: str, session_id: str, *messages: str) -> None:
        """Add plain-text messages from a single peer to a session."""
        peer = self._client.peer(peer_id)
        session = self._client.session(session_id)
        session.add_messages([peer.message(m) for m in messages])

    def recall(self, peer_id: str, query: str) -> Optional[str]:
        """Query what Honcho knows about a peer with a natural language question."""
        peer = self._client.peer(peer_id)
        return peer.chat(query)

    def peers(self):
        return self._client.peers()

    def sessions(self):
        return self._client.sessions()


def get_memory(workspace_id: str = DEFAULT_WORKSPACE) -> ProjectMemory:
    return ProjectMemory(workspace_id=workspace_id)
