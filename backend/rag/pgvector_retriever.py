"""
PostgreSQL + pgvector retriever.

This is the production retrieval adapter for environments where documents are
stored in PostgreSQL rather than the local Chroma demo store.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.rag.chunker import TextChunk
from backend.rag.embedder import EmbeddingVector
from backend.rag.retriever import RetrievedChunk, RetrieverProtocol, risk_level_for_text
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PGVectorRetriever(RetrieverProtocol):
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def count(self) -> int:
        with self._session_factory() as session:
            return int(
                session.execute(
                    text("SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL")
                ).scalar_one()
            )

    def index_chunks(
        self,
        chunks: list[TextChunk],
        embeddings: list[EmbeddingVector],
        original_filename: str,
    ) -> None:
        if not chunks:
            return
        with self._session_factory() as session:
            for chunk, embedding in zip(chunks, embeddings):
                session.execute(
                    text(
                        """
                        INSERT INTO documents (
                            id, original_filename, stored_filename, file_size_bytes,
                            chunk_count, status, content_text, risk_level, embedding, processed_at
                        )
                        VALUES (
                            :id, :original_filename, :stored_filename, :file_size_bytes,
                            1, 'ready', :content_text, :risk_level, CAST(:embedding AS vector), NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            content_text = EXCLUDED.content_text,
                            risk_level = EXCLUDED.risk_level,
                            embedding = EXCLUDED.embedding,
                            status = 'ready',
                            processed_at = NOW()
                        """
                    ),
                    {
                        "id": f"{chunk.doc_id}_chunk_{chunk.chunk_index}",
                        "original_filename": original_filename,
                        "stored_filename": original_filename,
                        "file_size_bytes": len(chunk.text.encode("utf-8")),
                        "content_text": chunk.text,
                        "risk_level": risk_level_for_text(chunk.text),
                        "embedding": _vector_literal(embedding),
                    },
                )
            session.commit()
        logger.info("PGVector indexed: filename=%s chunks=%d", original_filename, len(chunks))

    def search(self, query_embedding: EmbeddingVector, top_k: int = 5) -> list[RetrievedChunk]:
        with self._session_factory() as session:
            rows: list[Any] = list(
                session.execute(
                    text(
                        """
                        SELECT
                            id,
                            original_filename,
                            content_text,
                            risk_level,
                            1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity_score
                        FROM documents
                        WHERE embedding IS NOT NULL
                          AND content_text IS NOT NULL
                        ORDER BY embedding <=> CAST(:query_embedding AS vector)
                        LIMIT :top_k
                        """
                    ),
                    {
                        "query_embedding": _vector_literal(query_embedding),
                        "top_k": top_k,
                    },
                )
            )

        return [
            RetrievedChunk(
                text=row.content_text,
                doc_id=row.id,
                chunk_index=_chunk_index(row.id),
                original_filename=row.original_filename,
                similarity_score=round(float(row.similarity_score or 0.0), 4),
                metadata={"risk_level": str(row.risk_level or "LOW")},
            )
            for row in rows
        ]

    def delete_document(self, doc_id: str) -> int:
        with self._session_factory() as session:
            result = session.execute(
                text("DELETE FROM documents WHERE id = :doc_id OR id LIKE :chunk_prefix"),
                {"doc_id": doc_id, "chunk_prefix": f"{doc_id}_chunk_%"},
            )
            session.commit()
            return int(result.rowcount or 0)


def _vector_literal(values: EmbeddingVector) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def _chunk_index(doc_id: str) -> int:
    try:
        return int(doc_id.rsplit("_chunk_", 1)[1])
    except (IndexError, ValueError):
        return 0


_instance: RetrieverProtocol | None = None


def initialize_pgvector_retriever(
    session_factory: Callable[[], Session],
) -> RetrieverProtocol:
    global _instance
    _instance = PGVectorRetriever(session_factory)
    return _instance


def get_pgvector_retriever() -> RetrieverProtocol:
    if _instance is None:
        raise RuntimeError("PGVector retriever not initialized.")
    return _instance
