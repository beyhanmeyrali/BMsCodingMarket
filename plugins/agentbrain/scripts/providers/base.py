"""
AgentBrain Provider Interfaces

Abstract base classes for vector database and embedding providers.
All concrete implementations must inherit from these interfaces.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class TrustMetadata:
    """
    Trust and governance metadata for memories.

    Enables enterprise-grade memory management with approval tracking,
    validation, and provenance chains.
    """
    source_type: str = "manual"  # manual, pr, adr, incident, conversation, auto_captured
    approval_status: str = "draft"  # draft, approved, archived, superseded
    confidence: float = 0.5  # 0.0 to 1.0
    last_validated: Optional[int] = None  # Unix timestamp
    owner: str = ""  # User or team responsible
    supersedes: Optional[str] = None  # ID of memory this replaces
    superseded_by: Optional[str] = None  # ID of memory that replaces this

    def is_trusted(self) -> bool:
        """Check if memory is trusted (approved and validated)."""
        return self.approval_status == "approved" and self.confidence >= 0.7

    def is_stale(self, max_age_seconds: int = 7776000) -> bool:
        """Check if memory is stale (90 days default)."""
        if self.last_validated is None:
            return True
        return (int(time.time()) - self.last_validated) > max_age_seconds


@dataclass
class Memory:
    """A memory stored in the vector database."""
    file_path: str
    scope: str
    type: str  # user, feedback, project, reference
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    domain_tags: List[str] = field(default_factory=list)  # Technical/domain tags
    trust: TrustMetadata = field(default_factory=TrustMetadata)

    def __post_init__(self):
        """Validate memory fields."""
        valid_types = {"user", "feedback", "project", "reference"}
        if self.type not in valid_types:
            raise ValueError(f"Invalid memory type: {self.type}. Must be one of {valid_types}")

        # Convert trust dict to TrustMetadata if needed
        if isinstance(self.trust, dict):
            self.trust = TrustMetadata(**{k: v for k, v in self.trust.items() if v is not None})


@dataclass
class SearchResult:
    """A result from a vector search query."""
    memory: Memory
    score: float
    id: str


class VectorDBProvider(ABC):
    """
    Abstract interface for vector database providers.

    Implementations must support:
    - Upsert (write/update)
    - Query with scope filtering
    - Delete by ID
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider (create collections, etc.)."""
        pass

    @abstractmethod
    def upsert(self, memory: Memory) -> str:
        """
        Write or update a memory.

        Returns:
            The ID of the upserted memory.
        """
        pass

    @abstractmethod
    def query(
        self,
        embedding: List[float],
        scopes: List[str],
        top_k: int = 8,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Query memories with scope filtering.

        Args:
            embedding: Query vector
            scopes: Allowed scopes (e.g., ["user:bob", "team:platform"])
            top_k: Maximum number of results
            min_score: Minimum similarity score

        Returns:
            List of search results sorted by score (descending).
        """
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    def get_by_id(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a memory by ID.

        Returns:
            The memory if found, None otherwise.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        pass


class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding providers.

    Implementations must support:
    - Single text embedding
    - Batch embedding
    - Dimension introspection
    """

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as a list of floats.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors.
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.

        Returns:
            Embedding dimension (e.g., 768 for qwen3:0.6b).
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        pass
