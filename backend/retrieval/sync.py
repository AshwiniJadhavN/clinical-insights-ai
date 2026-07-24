"""Bi-directional retrieval sync between ChromaDB and PGVector."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from sqlalchemy.orm import Session

from backend.config import Settings
from backend.rag.chunker import TextChunk
from backend.rag.embedder import EmbeddingVector
from backend.rag.pgvector_retriever import PGVectorRetriever
from backend.rag.retriever import ChromaRetriever, RetrievedChunk, RetrieverProtocol
from backend.utils.logger import get_logger

logger = get_logger(__name__)

SyncMode = Literal["DUAL_WRITE", "PG_ONLY"]


class SyncedRetriever(RetrieverProtocol):
    def __init__(
        self,
        mode: SyncMode,
        pgvector: RetrieverProtocol | None,
        chroma: RetrieverProtocol | None,
    ) -> None:
        if mode == "PG_ONLY" and pgvector is None:
            raise RuntimeError("SYNC_MODE=PG_ONLY requires PGVector to be available.")
        if mode == "DUAL_WRITE" and pgvector is None and chroma is None:
            raise RuntimeError("SYNC_MODE=DUAL_WRITE requires at least one vector store.")
        self._mode = mode
        self._pgvector = pgvector
        self._chroma = chroma

    def count(self) -> int:
        if self._pgvector:
            try:
                return self._pgvector.count()
            except Exception as exc:
                if self._mode == "PG_ONLY":
                    raise
                logger.warning("PGVector count failed, falling back to Chroma: %s", type(exc).__name__)
        return self._chroma.count() if self._chroma else 0

    def index_chunks(
        self,
        chunks: list[TextChunk],
        embeddings: list[EmbeddingVector],
        original_filename: str,
    ) -> None:
        errors: list[Exception] = []
        if self._pgvector:
            try:
                self._pgvector.index_chunks(chunks, embeddings, original_filename)
            except Exception as exc:
                errors.append(exc)
                logger.warning("PGVector index failed: %s", type(exc).__name__)
        if self._mode == "DUAL_WRITE" and self._chroma:
            try:
                self._chroma.index_chunks(chunks, embeddings, original_filename)
            except Exception as exc:
                errors.append(exc)
                logger.warning("Chroma index failed: %s", type(exc).__name__)
        if self._mode == "PG_ONLY" and errors:
            raise errors[0]

    def search(self, query_embedding: EmbeddingVector, top_k: int) -> list[RetrievedChunk]:
        if self._pgvector:
            try:
                results = self._pgvector.search(query_embedding, top_k)
                if results or self._mode == "PG_ONLY":
                    return results
            except Exception as exc:
                if self._mode == "PG_ONLY":
                    raise
                logger.warning("PGVector search failed, falling back to Chroma: %s", type(exc).__name__)
        return self._chroma.search(query_embedding, top_k) if self._chroma else []

    def delete_document(self, doc_id: str) -> int:
        removed = 0
        if self._pgvector:
            removed += self._pgvector.delete_document(doc_id)
        if self._mode == "DUAL_WRITE" and self._chroma:
            removed += self._chroma.delete_document(doc_id)
        return removed


_instance: RetrieverProtocol | None = None


def initialize_retrieval_sync(
    settings: Settings,
    session_factory: Callable[[], Session] | None,
) -> RetrieverProtocol:
    global _instance
    mode = _sync_mode(settings.sync_mode)
    pgvector = PGVectorRetriever(session_factory) if session_factory else None
    chroma = None
    if mode == "DUAL_WRITE":
        chroma = ChromaRetriever(
            settings.chroma_persist_directory,
            settings.chroma_collection_name,
        )
    _instance = SyncedRetriever(mode=mode, pgvector=pgvector, chroma=chroma)
    return _instance


def get_sync_retriever() -> RetrieverProtocol:
    if _instance is None:
        raise RuntimeError("Retrieval sync not initialized.")
    return _instance


def _sync_mode(value: str) -> SyncMode:
    normalized = value.upper()
    if normalized not in {"DUAL_WRITE", "PG_ONLY"}:
        raise ValueError("SYNC_MODE must be either DUAL_WRITE or PG_ONLY.")
    return normalized  # type: ignore[return-value]
