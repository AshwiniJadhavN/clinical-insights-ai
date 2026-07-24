"""
Sentence-transformers embedding wrapper.

Provides:
  EmbedderProtocol              — duck-typed interface
  SentenceTransformerEmbedder   — production implementation
  FakeEmbedder                  — deterministic test double (no model download)
  initialize_embedder()         — load model at startup, store as singleton
  get_embedder()                — return cached singleton (raises if not initialized)

HIPAA:
  Log only: model name, batch size, embedding dimension — never text content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from backend.utils.logger import get_logger

logger = get_logger(__name__)

EmbeddingVector = list[float]


@runtime_checkable
class EmbedderProtocol(Protocol):
    @property
    def dimension(self) -> int: ...
    @property
    def model_name(self) -> str: ...
    def embed(self, text: str) -> EmbeddingVector: ...
    def embed_batch(self, texts: list[str]) -> list[EmbeddingVector]: ...


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[EmbeddingVector]
    model: str
    dimension: int
    count: int


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            self._dim: int = self._model.get_sentence_embedding_dimension()
            logger.info("Embedder ready: model=%s dim=%d", model_name, self._dim)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model '{model_name}'. "
                "Ensure sentence-transformers is installed and the model name is valid."
            ) from exc

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(self, text: str) -> EmbeddingVector:
        vector = self._model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[EmbeddingVector]:
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        logger.info("Embedded batch: model=%s count=%d dim=%d", self._model_name, len(texts), self._dim)
        return vectors.tolist()  # type: ignore[return-value]


class FakeEmbedder:
    """Deterministic test double for EmbedderProtocol. No model download."""

    _DIM: int = 384

    @property
    def dimension(self) -> int:
        return self._DIM

    @property
    def model_name(self) -> str:
        return "fake-embedder-for-testing"

    def embed(self, text: str) -> EmbeddingVector:
        import random
        rng = random.Random(hash(text))
        return [rng.random() for _ in range(self._DIM)]

    def embed_batch(self, texts: list[str]) -> list[EmbeddingVector]:
        return [self.embed(t) for t in texts]


_instance: EmbedderProtocol | None = None


def initialize_embedder(model_name: str = "all-MiniLM-L6-v2") -> EmbedderProtocol:
    global _instance
    _instance = SentenceTransformerEmbedder(model_name)
    return _instance


def get_embedder() -> EmbedderProtocol:
    if _instance is None:
        raise RuntimeError(
            "Embedder not initialized. "
            "Call initialize_embedder() in the application lifespan handler."
        )
    return _instance
