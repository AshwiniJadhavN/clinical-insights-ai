"""
ChromaDB vector retriever.

Provides index_chunks(), search(), delete_document(), count().
Protocol + FakeRetriever test double for offline testing.

HIPAA: Log only doc_id, chunk counts, similarity scores. Never log chunk text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from backend.rag.chunker import TextChunk
from backend.rag.embedder import EmbeddingVector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    doc_id: str
    chunk_index: int
    original_filename: str
    similarity_score: float
    start_char: int = 0
    end_char: int = 0
    metadata: dict[str, str] | None = None


@runtime_checkable
class RetrieverProtocol(Protocol):
    def count(self) -> int: ...
    def index_chunks(self, chunks: list[TextChunk], embeddings: list[EmbeddingVector], original_filename: str) -> None: ...
    def search(self, query_embedding: EmbeddingVector, top_k: int) -> list[RetrievedChunk]: ...
    def delete_document(self, doc_id: str) -> int: ...


class ChromaRetriever:
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB ready: collection=%s chunks=%d", collection_name, self._collection.count())
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize ChromaDB at '{persist_dir}'.") from exc

    def count(self) -> int:
        return self._collection.count()

    def index_chunks(self, chunks: list[TextChunk], embeddings: list[EmbeddingVector], original_filename: str) -> None:
        if not chunks:
            return
        ids = [f"{c.doc_id}_chunk_{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {"doc_id": c.doc_id, "chunk_index": c.chunk_index,
             "original_filename": original_filename,
             "start_char": c.start_char, "end_char": c.end_char,
             "risk_level": risk_level_for_text(c.text)}
            for c in chunks
        ]
        self._collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)  # type: ignore[arg-type]
        logger.info("Indexed: doc_id=%s chunks=%d", chunks[0].doc_id, len(chunks))

    def search(self, query_embedding: EmbeddingVector, top_k: int = 5) -> list[RetrievedChunk]:
        total = self._collection.count()
        if total == 0:
            return []
        results = self._collection.query(
            query_embeddings=[query_embedding],  # type: ignore[arg-type]
            n_results=min(top_k, total),
            include=["documents", "metadatas", "distances"],
        )
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        retrieved = [
            RetrievedChunk(
                text=doc_text, doc_id=meta.get("doc_id", ""),
                chunk_index=int(meta.get("chunk_index", 0)),
                original_filename=meta.get("original_filename", "unknown"),
                similarity_score=round(max(0.0, 1.0 - float(dist)), 4),
                start_char=int(meta.get("start_char", 0)),
                end_char=int(meta.get("end_char", 0)),
                metadata={"risk_level": str(meta.get("risk_level", "LOW"))},
            )
            for doc_text, meta, dist in zip(docs, metas, dists)
        ]
        logger.info("Search: top_k=%d results=%d", top_k, len(retrieved))
        return retrieved

    def delete_document(self, doc_id: str) -> int:
        existing = self._collection.get(where={"doc_id": doc_id}, include=[])
        ids_to_delete: list[str] = existing.get("ids", [])
        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
        logger.info("Removed from index: doc_id=%s chunks=%d", doc_id, len(ids_to_delete))
        return len(ids_to_delete)


class FakeRetriever:
    """Deterministic in-memory test double for RetrieverProtocol."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[TextChunk, EmbeddingVector, str]] = {}

    def count(self) -> int:
        return len(self._store)

    def index_chunks(self, chunks: list[TextChunk], embeddings: list[EmbeddingVector], original_filename: str) -> None:
        for chunk, vec in zip(chunks, embeddings):
            self._store[f"{chunk.doc_id}_chunk_{chunk.chunk_index}"] = (chunk, vec, original_filename)

    def search(self, query_embedding: EmbeddingVector, top_k: int = 5) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(text=chunk.text, doc_id=chunk.doc_id, chunk_index=chunk.chunk_index,
                           original_filename=fname, similarity_score=0.85,
                           metadata={"risk_level": risk_level_for_text(chunk.text)})
            for chunk, _, fname in list(self._store.values())[:top_k]
        ]

    def delete_document(self, doc_id: str) -> int:
        keys = [k for k in self._store if k.startswith(f"{doc_id}_")]
        for k in keys:
            del self._store[k]
        return len(keys)


_instance: RetrieverProtocol | None = None


def initialize_retriever(persist_dir: str, collection_name: str) -> RetrieverProtocol:
    global _instance
    _instance = ChromaRetriever(persist_dir, collection_name)
    return _instance


def get_retriever() -> RetrieverProtocol:
    if _instance is None:
        raise RuntimeError(
            "Retriever not initialized. "
            "Call initialize_retriever() in the application lifespan handler."
        )
    return _instance


def risk_level_for_text(text: str) -> str:
    lowered = text.lower()
    high_terms = ("pediatric", "paediatric", "oncology", "cancer", "chemotherapy", "terminal")
    medium_terms = ("pregnancy", "renal", "cardiac", "hypoglycemia", "potassium", "adverse")
    if any(term in lowered for term in high_terms):
        return "HIGH"
    if any(term in lowered for term in medium_terms):
        return "MEDIUM"
    return "LOW"
