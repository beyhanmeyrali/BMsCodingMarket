"""
Ollama Embedding Provider for AgentBrain

Generates embeddings using local Ollama models.
Supports qwen3:0.6b, nomic-embed-text, bge-small, and other Ollama embedding models.
"""

import requests
from typing import List
import time


class OllamaEmbedError(Exception):
    """Raised when Ollama embedding fails."""
    pass


class OllamaEmbedder:
    """
    Ollama-based embedding provider.

    Features:
    - Local inference (no API costs)
    - Multiple model support
    - Batch embedding
    - Health checking
    """

    # Known embedding dimensions for common models
    MODEL_DIMENSIONS = {
        "qwen3-embedding": 1024,
        "qwen3-embedding:0.6b": 1024,
        "qwen3:0.6b": 768,
        "qwen3:0.6b-f16": 768,
        "nomic-embed-text": 768,
        "nomic-embed-text:v1.5": 768,
        "bge-small-en-v1.5": 384,
        "bge-base-en": 768,
        "bge-large": 1024,
        "all-minilm": 384,
        "all-minilm:l6-v2": 384,
        "mxbai-embed-large": 1024,
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:0.6b",
        timeout: int = 30,
    ):
        """
        Initialize Ollama embedder.

        Args:
            base_url: Ollama API base URL
            model: Model name (must be pulled in Ollama first)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._dimension = self._get_model_dimension(model)

        # Verify Ollama is running on init
        if not self.health_check():
            raise OllamaEmbedError(
                f"Ollama not available at {base_url}. "
                f"Start Ollama with: ollama serve"
            )

        # Verify model is available
        if not self._model_exists():
            raise OllamaEmbedError(
                f"Model '{model}' not found in Ollama. "
                f"Pull it with: ollama pull {model}"
            )

    def _get_model_dimension(self, model: str) -> int:
        """Get embedding dimension for a model."""
        # Try exact match first
        if model in self.MODEL_DIMENSIONS:
            return self.MODEL_DIMENSIONS[model]

        # Try prefix match (e.g., "qwen3:0.6b" matches "qwen3:0.6b-f16")
        for known_model, dim in self.MODEL_DIMENSIONS.items():
            if model.startswith(known_model.split(":")[0]):
                return dim

        # Default to 768 (common for most embedding models)
        return 768

    def _model_exists(self) -> bool:
        """Check if the model is available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            # Check for exact or partial match
            return any(self.model in name for name in model_names)
        except Exception:
            return False

    def health_check(self) -> bool:
        """
        Check if Ollama is running.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_dimension(self) -> int:
        """
        Get the embedding dimension.

        Returns:
            Dimension of embedding vectors.
        """
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as a list of floats.
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self._dimension

        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            embedding = result.get("embedding")

            if not embedding:
                raise OllamaEmbedError("No embedding in response")

            if len(embedding) != self._dimension:
                raise OllamaEmbedError(
                    f"Embedding dimension mismatch: "
                    f"expected {self._dimension}, got {len(embedding)}"
                )

            return embedding

        except requests.RequestException as e:
            raise OllamaEmbedError(f"Ollama request failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors.
        """
        # For now, use sequential requests
        # Ollama doesn't have a true batch endpoint
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings

    def embed_with_retry(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Generate embedding with retry logic.

        Args:
            text: Input text to embed
            max_retries: Maximum number of retry attempts

        Returns:
            Embedding vector.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.embed(text)
            except OllamaEmbedError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry

        raise OllamaEmbedError(f"Failed after {max_retries} attempts: {last_error}")
