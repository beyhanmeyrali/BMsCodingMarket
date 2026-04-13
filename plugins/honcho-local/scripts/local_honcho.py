"""
Local Honcho-like Memory Provider

A simplified local implementation of Honcho's memory and reasoning concepts
using Ollama for local LLM support. This provides:

- Peer-based user/agent modeling
- Session management
- Message storage with context retrieval
- Natural language queries about users
- Vector search for similar messages

All running locally with Ollama - no API keys needed.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, asdict, field
from pathlib import Path
import hashlib

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


@dataclass
class Message:
    """A message in a conversation."""
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Peer:
    """A peer (user or agent) in the system."""
    id: str
    name: str
    peer_type: Literal["user", "agent"]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LocalHoncho:
    """
    Local Honcho-like memory provider using Ollama and optionally Postgres.

    This implements Honcho's core concepts locally:
    - Workspaces: Isolated containers for apps
    - Peers: Users and agents
    - Sessions: Conversation threads
    - Messages: Data units with optional reasoning
    """

    def __init__(
        self,
        workspace_id: str = "local-workspace",
        db_path: str = None,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "qwen3.5:9b",
        embedding_model: str = "qwen3-embedding:0.6b",
        use_postgres: bool = False,
        postgres_uri: str = "",
        think: bool | Literal["low", "medium", "high"] = False,
    ):
        """
        Initialize LocalHoncho.

        Args:
            workspace_id: Workspace identifier
            db_path: Path to JSON storage file (or use Postgres)
            ollama_base_url: Ollama API endpoint
            model: Ollama model to use (qwen3.5:9b, qwen3:8b, deepseek-r1 support thinking)
            embedding_model: Ollama embedding model (qwen3-embedding:0.6b)
            use_postgres: Use Postgres instead of JSON storage
            postgres_uri: Postgres connection string
            think: Enable thinking mode (True/False, or "low"/"medium"/"high" for GPT-OSS)
        """
        self.workspace_id = workspace_id
        # Default to honcho_data folder if no db_path provided
        if db_path is None:
            db_path = f"honcho_data/honco_{workspace_id}.json"

        self.db_path = Path(db_path)
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.embedding_model = embedding_model
        self.use_postgres = use_postgres
        self.think = think

        # Initialize storage
        self._storage: Dict[str, Any] = {
            "workspaces": {},
            "peers": {},
            "sessions": {},
            "messages": {},
            "representations": {},  # Cached user representations
        }

        # Initialize Ollama client
        if OLLAMA_AVAILABLE:
            self.client = ollama.Client(host=ollama_base_url)
        else:
            self.client = None
            print("[WARNING] Ollama not available. Install with: pip install ollama")

        # Initialize Postgres if requested
        self.conn = None
        if use_postgres and PSYCOPG2_AVAILABLE and postgres_uri:
            try:
                self.conn = psycopg2.connect(postgres_uri)
                self._init_postgres_tables()
            except Exception as e:
                print(f"[WARNING] Failed to connect to Postgres: {e}")
                self.use_postgres = False

        # Load existing data
        if not self.use_postgres:
            self._load_storage()

    def _load_storage(self):
        """Load storage from JSON file."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self._storage = json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load storage: {e}")

    def _save_storage(self):
        """Save storage to JSON file."""
        if not self.use_postgres:
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    json.dump(self._storage, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[ERROR] Failed to save storage: {e}")

    def _init_postgres_tables(self):
        """Initialize Postgres tables."""
        if not self.conn:
            return

        cur = self.conn.cursor()
        tables = [
            """CREATE TABLE IF NOT EXISTS honcho_peers (
                id VARCHAR(255) PRIMARY KEY,
                workspace_id VARCHAR(255),
                name VARCHAR(255),
                peer_type VARCHAR(50),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS honcho_sessions (
                id VARCHAR(255) PRIMARY KEY,
                workspace_id VARCHAR(255),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS honcho_messages (
                id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255),
                peer_id VARCHAR(255),
                role VARCHAR(50),
                content TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]
        for table in tables:
            try:
                cur.execute(table)
            except Exception as e:
                print(f"[WARNING] Table creation error: {e}")
        self.conn.commit()

    # Workspace operations
    def workspace(self, workspace_id: str) -> "LocalHoncho":
        """Get or create a workspace."""
        new_instance = LocalHoncho(
            workspace_id=workspace_id,
            db_path=str(self.db_path),
            ollama_base_url=self.ollama_base_url,
            model=self.model,
            embedding_model=self.embedding_model,
            use_postgres=self.use_postgres,
            postgres_uri=self.conn.dsn if self.conn else "",
            think=self.think,
        )
        new_instance._storage = self._storage
        return new_instance

    # Peer operations
    def peer(self, peer_id: str, name: str = None, peer_type: Literal["user", "agent"] = "user") -> Peer:
        """Get or create a peer."""
        peer_key = f"{self.workspace_id}:{peer_id}"

        if peer_key not in self._storage["peers"]:
            peer = Peer(
                id=peer_id,
                name=name or peer_id,
                peer_type=peer_type,
            )
            self._storage["peers"][peer_key] = asdict(peer)
            self._save_storage()
        else:
            peer_data = self._storage["peers"][peer_key]
            peer = Peer(**peer_data)

        return peer

    # Session operations
    def session(self, session_id: str, metadata: Dict[str, Any] = None) -> "Session":
        """Get or create a session."""
        return Session(
            honcho=self,
            session_id=session_id,
            metadata=metadata or {},
        )

    # Message operations
    def add_message(self, session_id: str, peer_id: str, role: str, content: str, metadata: Dict = None) -> Message:
        """Add a message to a session."""
        import uuid
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        key = f"{self.workspace_id}:{session_id}"
        if key not in self._storage["messages"]:
            self._storage["messages"][key] = []

        self._storage["messages"][key].append(asdict(message))
        self._save_storage()
        return message

    def get_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a session."""
        key = f"{self.workspace_id}:{session_id}"
        messages = self._storage.get("messages", {}).get(key, [])
        return [Message(**m) for m in messages[-limit:]]

    # Chat/Query operations
    def chat(
        self,
        peer_id: str,
        question: str,
        include_thinking: bool = False,
    ) -> str | Dict[str, str]:
        """
        Ask a natural language question about a peer.

        This analyzes the peer's conversation history and provides insights.

        Args:
            peer_id: The peer to ask about
            question: The question to answer
            include_thinking: If True, return dict with 'thinking' and 'content' keys

        Returns:
            String response, or dict with 'thinking' and 'content' if include_thinking=True
        """
        if not self.client:
            return "[ERROR] Ollama not available"

        # Gather peer context
        peer_key = f"{self.workspace_id}:{peer_id}"
        context_parts = []

        # Get all messages for this peer
        for session_key, messages in self._storage.get("messages", {}).items():
            for msg in messages:
                context_parts.append(f"{msg['role']}: {msg['content']}")

        context = "\n".join(context_parts[-50:])  # Last 50 messages

        # Build query prompt
        prompt = f"""You are analyzing a user's behavior based on their conversation history.

Conversation History:
{context}

Question: {question}

Provide a concise, helpful answer based on the conversation history above."""

        try:
            # Build chat kwargs
            chat_kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant analyzing user behavior."},
                    {"role": "user", "content": prompt}
                ]
            }

            # Add think parameter if enabled
            if self.think:
                chat_kwargs["think"] = self.think

            response = self.client.chat(**chat_kwargs)

            message = response.get("message", {})
            thinking = message.get("thinking", "")
            content = message.get("content", "No response")

            if include_thinking and thinking:
                return {"thinking": thinking, "content": content}

            return content
        except Exception as e:
            return f"[ERROR] {e}"

    def search(self, peer_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for similar messages using semantic search with embeddings.

        Uses qwen3-embedding:0.6b for vector similarity search.
        Searches across ALL sessions for messages from this peer.
        """
        if not self.client:
            return [{"error": "Ollama not available"}]

        # Get all messages for this peer across all sessions
        all_messages = []
        for session_key, messages in self._storage.get("messages", {}).items():
            for msg in messages:
                # Check if this message is from the specified peer
                # Messages store peer_id in metadata
                msg_peer_id = msg.get("metadata", {}).get("peer_id", "")
                if msg_peer_id == peer_id:
                    all_messages.append(msg)

        if not all_messages:
            return [{"query": query, "results": "No messages found for this peer"}]

        try:
            # Get query embedding
            query_response = self.client.embed(model=self.embedding_model, input=query)
            query_embedding = query_response.get("embeddings", [[]])[0]

            if not query_embedding or len(query_embedding) == 0:
                # Fallback to keyword search if embedding fails
                query_lower = query.lower()
                results = []
                for msg in all_messages:
                    content = msg.get("content", "")
                    if query_lower in content.lower():
                        results.append({
                            "content": content,
                            "timestamp": msg.get("timestamp"),
                            "score": 1.0,
                        })
                return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:limit]

            # Get embeddings for all messages and calculate similarity
            results = []
            for msg in all_messages:
                content = msg.get("content", "")
                if not content:
                    continue

                try:
                    msg_response = self.client.embed(model=self.embedding_model, input=content)
                    msg_embedding = msg_response.get("embeddings", [[]])[0]

                    if msg_embedding and len(msg_embedding) > 0:
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(query_embedding, msg_embedding)
                        # Lower threshold for better results
                        if similarity > 0.1:
                            results.append({
                                "content": content,
                                "timestamp": msg.get("timestamp"),
                                "score": similarity,
                            })
                except Exception as e:
                    # Skip messages that fail to embed, but log it
                    print(f"[WARNING] Failed to embed message: {e}")
                    continue

            # Sort by similarity score
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results[:limit]

        except Exception as e:
            # Fallback to keyword search on error
            query_lower = query.lower()
            fallback_results = []
            for msg in all_messages:
                content = msg.get("content", "")
                if query_lower in content.lower():
                    fallback_results.append({
                        "content": content,
                        "timestamp": msg.get("timestamp"),
                        "score": 0.5,
                    })
            return fallback_results[:limit]

        except Exception as e:
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results[:limit]

        except Exception as e:
            # Fallback to keyword search on error
            query_lower = query.lower()
            results = []
            for msg in all_messages:
                content = msg.get("content", "")
                if query_lower in content.lower():
                    results.append({
                        "content": content,
                        "timestamp": msg.get("timestamp"),
                        "score": 0.5,
                    })
            return results[:limit]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(y * y for y in b))
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)

    def get_representation(self, peer_id: str, session_id: str = None, include_thinking: bool = False) -> Dict[str, Any]:
        """
        Get a representation (profile) of a peer.

        This analyzes the peer's behavior and creates a summary profile.

        Args:
            peer_id: The peer to analyze
            session_id: Optional session to limit analysis to
            include_thinking: If True, include 'thinking' in the result

        Returns:
            Dictionary with profile data, optionally including 'thinking'
        """
        peer_key = f"{self.workspace_id}:{peer_id}"

        # Check cache
        cache_key = f"{peer_key}:{session_id or 'all'}"
        if cache_key in self._storage.get("representations", {}):
            cached = self._storage["representations"][cache_key]
            # Still return thinking if requested and it was cached
            if include_thinking and self.think and "thinking" not in cached:
                # Regenerate if thinking was requested but not in cache
                pass
            else:
                return cached

        if not self.client:
            return {"peer_id": peer_id, "error": "Ollama not available"}

        # Gather context
        context_parts = []
        for session_key, messages in self._storage.get("messages", {}).items():
            if session_id is None or session_key.endswith(session_id):
                for msg in messages:
                    context_parts.append(f"{msg['role']}: {msg['content']}")

        context = "\n".join(context_parts[-100:])

        prompt = f"""Analyze this user's conversation history and create a profile.

Conversation:
{context}

Provide a JSON profile with:
- interests: list of topics they're interested in
- communication_style: brief description
- frequent_topics: list of common topics
- sentiment: overall tone (positive/neutral/negative)

Respond with valid JSON only."""

        try:
            # Build chat kwargs
            chat_kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ]
            }

            # Add think parameter if enabled
            if self.think:
                chat_kwargs["think"] = self.think

            response = self.client.chat(**chat_kwargs)

            message = response.get("message", {})
            content = message.get("content", "{}")
            thinking = message.get("thinking", "")

            # Try to parse as JSON
            try:
                representation = json.loads(content)
            except:
                representation = {"raw_response": content}

            # Cache it
            if "representations" not in self._storage:
                self._storage["representations"] = {}
            self._storage["representations"][cache_key] = representation
            self._save_storage()

            return representation
        except Exception as e:
            return {"peer_id": peer_id, "error": str(e)}


class Session:
    """A session (conversation thread) between peers."""

    def __init__(self, honcho: LocalHoncho, session_id: str, metadata: Dict[str, Any] = None):
        self.honcho = honcho
        self.session_id = session_id
        self.metadata = metadata or {}

    def add_messages(self, messages: List[Dict]) -> int:
        """
        Add messages to the session.

        Args:
            messages: List of message dicts or Message objects

        Returns:
            Number of messages added
        """
        count = 0
        for msg in messages:
            if isinstance(msg, dict):
                peer_id = msg.get("metadata", {}).get("peer_id", "unknown")
                role = msg.get("role", "user")
                content = msg.get("content", "")
                metadata = msg.get("metadata", {})

                self.honcho.add_message(
                    session_id=self.session_id,
                    peer_id=peer_id,
                    role=role,
                    content=content,
                    metadata=metadata
                )
                count += 1
        return count

    def get_context(self, summary: bool = False, tokens: int = 10000, include_thinking: bool = False) -> str | Dict[str, str]:
        """
        Get conversation context.

        Args:
            summary: Include summary (requires LLM)
            tokens: Approximate token limit
            include_thinking: If True, return dict with 'thinking' and 'content' keys

        Returns:
            Formatted context string, or dict with 'thinking' and 'content' if include_thinking=True and summary=True
        """
        messages = self.honcho.get_messages(self.session_id)

        context_parts = []
        total_chars = 0
        char_limit = tokens * 4  # Rough estimate

        for msg in reversed(messages):
            line = f"{msg.role}: {msg.content}"
            if total_chars + len(line) > char_limit:
                break
            context_parts.insert(0, line)
            total_chars += len(line)

        result = "\n".join(context_parts)

        if summary and self.honcho.client:
            try:
                summary_prompt = f"""Summarize this conversation concisely:

{result}

Provide a brief summary covering:
1. Main topics discussed
2. Any actions or decisions made
3. Current state of the conversation"""

                # Build chat kwargs
                chat_kwargs = {
                    "model": self.honcho.model,
                    "messages": [{"role": "user", "content": summary_prompt}]
                }

                # Add think parameter if enabled
                if self.honcho.think:
                    chat_kwargs["think"] = self.honcho.think

                response = self.honcho.client.chat(**chat_kwargs)

                message = response.get("message", {})
                summary_text = message.get("content", "")
                thinking = message.get("thinking", "")

                if include_thinking and thinking:
                    return {
                        "thinking": thinking,
                        "content": f"Summary:\n{summary_text}\n\nRecent Messages:\n{result}"
                    }

                result = f"Summary:\n{summary_text}\n\nRecent Messages:\n{result}"
            except Exception as e:
                result = f"[Summary error: {e}]\n\n{result}"

        return result

    def representation(self, peer: Peer) -> Dict[str, Any]:
        """Get representation of a peer in this session context."""
        return self.honcho.get_representation(peer.id, self.session_id)


# Convenience function
def get_local_honcho(
    workspace_id: str = "local-workspace",
    ollama_base_url: str = "http://localhost:11434",
    model: str = "qwen3.5:9b",
    embedding_model: str = "qwen3-embedding:0.6b",
    use_postgres: bool = False,
    postgres_uri: str = "",
    think: bool | Literal["low", "medium", "high"] = False,
) -> LocalHoncho:
    """
    Factory function to get a LocalHoncho instance.

    Args:
        workspace_id: Workspace identifier
        ollama_base_url: Ollama API endpoint
        model: Ollama model to use (qwen3.5:9b supports thinking)
        embedding_model: Ollama embedding model for semantic search
        use_postgres: Use Postgres instead of JSON
        postgres_uri: Postgres connection string
        think: Enable thinking mode (True/False, or "low"/"medium"/"high" for GPT-OSS)

    Returns:
        LocalHoncho instance
    """
    return LocalHoncho(
        workspace_id=workspace_id,
        db_path=None,  # Will default to honcho_data/honco_{workspace_id}.json
        ollama_base_url=ollama_base_url,
        model=model,
        embedding_model=embedding_model,
        use_postgres=use_postgres,
        postgres_uri=postgres_uri,
        think=think,
    )


# Demo
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Local Honcho - Memory Provider with Ollama")
    print("=" * 60)

    # Check Ollama
    if not OLLAMA_AVAILABLE:
        print("[ERROR] Ollama Python client not installed.")
        print("Install with: pip install ollama")
        sys.exit(1)

    # Initialize (with thinking mode enabled for qwen3.5:9b)
    honcho = get_local_honcho(
        workspace_id="demo-workspace",
        model="qwen3.5:9b",
        think=True,  # Enable thinking mode
    )

    # Create peers
    user = honcho.peer("alice", name="Alice", peer_type="user")
    agent = honcho.peer("sap-agent", name="SAP Assistant", peer_type="agent")

    print(f"\n[OK] Created peers: {user.name} (user), {agent.name} (agent)")

    # Create session
    session = honcho.session("demo-session")

    # Add messages
    messages = [
        {"role": "user", "content": "I need to approve PO 4500012345", "metadata": {"peer_id": user.id}},
        {"role": "assistant", "content": "I can help with PO approval. Let me check the status.", "metadata": {"peer_id": agent.id}},
        {"role": "user", "content": "It's urgent, the vendor is waiting", "metadata": {"peer_id": user.id}},
        {"role": "assistant", "content": "PO 4500012345 is ready for approval. I'll process it now.", "metadata": {"peer_id": agent.id}},
    ]

    count = session.add_messages(messages)
    print(f"[OK] Added {count} messages to session")

    # Get context
    context = session.get_context(summary=True)
    print(f"\n--- Session Context ---\n{context}\n")

    # Chat about user (with thinking mode)
    print("\n--- Chat about user (with thinking) ---")
    response = honcho.chat(user.id, "What is this user trying to do?", include_thinking=True)
    if isinstance(response, dict):
        print(f"Thinking: {response.get('thinking', 'N/A')}")
        print(f"Answer: {response.get('content', 'N/A')}")
    else:
        print(f"Response: {response}")

    # Get representation (with thinking mode)
    print("\n--- User Representation ---")
    representation = honcho.get_representation(user.id, include_thinking=True)
    print(json.dumps(representation, indent=2))

    print("\n[SUCCESS] Local Honcho is working!")
