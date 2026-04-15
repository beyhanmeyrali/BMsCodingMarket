"""
Qdrant Vector Database Provider for AgentBrain

Implements vector storage with scope-based multi-tenancy.
Each memory is tagged with a scope (user:bob, team:platform, etc.)
and queries are filtered to only return allowed scopes.
"""

import hashlib
import time
from typing import List, Optional
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchAny,
    )
except ImportError:
    raise ImportError(
        "qdrant-client is required. Install with: pip install qdrant-client>=1.12.0"
    )

from .base import VectorDBProvider, Memory, SearchResult


class QdrantProvider(VectorDBProvider):
    """
    Qdrant-based vector database provider.

    Features:
    - Scope-based access control (user/team/project/org)
    - Automatic collection creation
    - Configurable embedding dimension
    - Health checking
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection: str = "agentbrain_memories",
        embedding_dim: int = 768,
        api_key: Optional[str] = None,
        timeout: int = 10,
    ):
        """
        Initialize Qdrant provider.

        Args:
            host: Qdrant server host
            port: Qdrant REST API port
            collection: Collection name
            embedding_dim: Embedding vector dimension
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            timeout=timeout,
        )
        self.collection = collection
        self.embedding_dim = embedding_dim
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the provider (create collection if not exists)."""
        if self._initialized:
            return

        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )

            # Create payload indexes for filtered fields
            # This improves query performance for scope filtering
            try:
                from qdrant_client.models import PayloadIndexParams, PayloadSchemaType

                self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name="scope",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                # Index creation might fail in older versions, that's ok
                pass

        self._initialized = True

    def _ensure_initialized(self):
        """Ensure collection is initialized."""
        if not self._initialized:
            self.initialize()

    def _generate_id(self, file_path: str) -> str:
        """Generate a stable ID from file path."""
        return hashlib.md5(file_path.encode("utf-8")).hexdigest()

    def upsert(self, memory: Memory) -> str:
        """
        Write or update a memory.

        Args:
            memory: Memory to upsert

        Returns:
            The ID of the upserted memory.
        """
        self._ensure_initialized()

        if memory.embedding is None:
            raise ValueError("Memory must have an embedding to upsert")

        memory_id = self._generate_id(memory.file_path)
        now = int(time.time())

        payload = {
            "file_path": memory.file_path,
            "scope": memory.scope,
            "type": memory.type,
            "content": memory.content,
            "created_at": memory.metadata.get("created_at", now),
            "updated_at": now,
            "provenance_weight": memory.metadata.get("provenance_weight", 0.5),
            "source": memory.metadata.get("source", "manual"),
            "author": memory.metadata.get("author", ""),
            "workspace": memory.metadata.get("workspace", ""),
            "pinned": memory.metadata.get("pinned", False),
        }

        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(
                id=memory_id,
                vector=memory.embedding,
                payload=payload,
            )],
        )

        return memory_id

    def query(
        self,
        embedding: List[float],
        scopes: List[str],
        top_k: int = 8,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """
        Query memories with mandatory scope filtering.

        Args:
            embedding: Query vector
            scopes: Allowed scopes (mandatory filter)
            top_k: Maximum results
            min_score: Minimum similarity score

        Returns:
            List of search results.
        """
        self._ensure_initialized()

        # Build mandatory scope filter
        scope_filter = Filter(
            must=[FieldCondition(
                key="scope",
                match=MatchAny(any=scopes),
            )]
        )

        results = self.client.search(
            collection_name=self.collection,
            query_vector=embedding,
            query_filter=scope_filter,
            limit=top_k,
            with_payload=True,
            score_threshold=min_score,
        )

        return [
            SearchResult(
                id=r.id,
                score=r.score,
                memory=Memory(
                    file_path=r.payload.get("file_path", ""),
                    scope=r.payload.get("scope", ""),
                    type=r.payload.get("type", ""),
                    content=r.payload.get("content", ""),
                    metadata=r.payload,
                ),
            )
            for r in results
        ]

    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: ID to delete

        Returns:
            True if deleted, False otherwise.
        """
        self._ensure_initialized()

        try:
            self.client.delete(
                collection_name=self.collection,
                points_selector=[memory_id],
            )
            return True
        except Exception:
            return False

    def get_by_id(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: ID to retrieve

        Returns:
            Memory if found, None otherwise.
        """
        self._ensure_initialized()

        try:
            result = self.client.retrieve(
                collection_name=self.collection,
                ids=[memory_id],
                with_payload=True,
            )

            if not result:
                return None

            payload = result[0].payload
            return Memory(
                file_path=payload.get("file_path", ""),
                scope=payload.get("scope", ""),
                type=payload.get("type", ""),
                content=payload.get("content", ""),
                metadata=payload,
            )
        except Exception:
            return None

    def health_check(self) -> bool:
        """
        Check if Qdrant is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def count(self) -> int:
        """
        Get total number of memories in the collection.

        Returns:
            Count of memories.
        """
        self._ensure_initialized()
        try:
            result = self.client.count(collection_name=self.collection)
            return result.count
        except Exception:
            return 0

    def clear_collection(self) -> bool:
        """
        Delete all memories from the collection.

        WARNING: This is destructive!

        Returns:
            True if successful, False otherwise.
        """
        self._ensure_initialized()
        try:
            # Delete and recreate collection (more reliable than filtered delete)
            from qdrant_client.models import VectorParams, Distance

            self.client.delete_collection(collection_name=self.collection)
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            # Recreate payload index
            try:
                from qdrant_client.models import PayloadIndexParams, PayloadSchemaType
                self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name="scope",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # Index creation is optional
            return True
        except Exception:
            return False
