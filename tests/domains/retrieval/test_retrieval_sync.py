import pytest

from backend.rag.chunker import TextChunk
from backend.rag.retriever import RetrievedChunk
from backend.retrieval.sync import SyncedRetriever


def test_synced_retriever_dual_writes_and_prefers_pgvector() -> None:
    pg = _Store(results=[_chunk("pg", 0.9)])
    chroma = _Store(results=[_chunk("chroma", 0.8)])
    retriever = SyncedRetriever(mode="DUAL_WRITE", pgvector=pg, chroma=chroma)
    chunks = [TextChunk(text="clinical evidence " * 4, chunk_index=0, start_char=0, end_char=72, doc_id="doc")]

    retriever.index_chunks(chunks, [[0.1]], "doc.txt")
    results = retriever.search([0.1], top_k=1)

    assert pg.indexed is True
    assert chroma.indexed is True
    assert results[0].doc_id == "pg"


def test_synced_retriever_falls_back_to_chroma_in_dual_write() -> None:
    retriever = SyncedRetriever(
        mode="DUAL_WRITE",
        pgvector=_Store(results=[], fail_search=True),
        chroma=_Store(results=[_chunk("chroma", 0.8)]),
    )

    results = retriever.search([0.1], top_k=1)

    assert results[0].doc_id == "chroma"


def test_synced_retriever_requires_pgvector_in_pg_only() -> None:
    with pytest.raises(RuntimeError):
        SyncedRetriever(mode="PG_ONLY", pgvector=None, chroma=_Store(results=[]))


def test_synced_retriever_raises_when_every_index_backend_fails() -> None:
    retriever = SyncedRetriever(
        mode="DUAL_WRITE",
        pgvector=_Store(results=[], fail_index=True),
        chroma=_Store(results=[], fail_index=True),
    )

    with pytest.raises(RuntimeError, match="all 2 configured vector stores"):
        retriever.index_chunks(
            [_text_chunk()],
            [[0.1]],
            "doc.txt",
        )


def test_synced_retriever_accepts_one_successful_index_backend() -> None:
    pg = _Store(results=[], fail_index=True)
    chroma = _Store(results=[])
    retriever = SyncedRetriever(mode="DUAL_WRITE", pgvector=pg, chroma=chroma)

    retriever.index_chunks([_text_chunk()], [[0.1]], "doc.txt")

    assert chroma.indexed is True


def _chunk(doc_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        text="text",
        doc_id=doc_id,
        chunk_index=0,
        original_filename="doc.txt",
        similarity_score=score,
    )


def _text_chunk() -> TextChunk:
    return TextChunk(
        text="clinical evidence " * 4,
        chunk_index=0,
        start_char=0,
        end_char=72,
        doc_id="doc",
    )


class _Store:
    def __init__(
        self,
        results: list[RetrievedChunk],
        fail_search: bool = False,
        fail_index: bool = False,
    ) -> None:
        self.results = results
        self.fail_search = fail_search
        self.fail_index = fail_index
        self.indexed = False

    def count(self) -> int:
        return len(self.results)

    def index_chunks(self, chunks, embeddings, original_filename: str) -> None:
        if self.fail_index:
            raise RuntimeError("index failed")
        self.indexed = True

    def search(self, query_embedding, top_k: int) -> list[RetrievedChunk]:
        if self.fail_search:
            raise RuntimeError("search failed")
        return self.results[:top_k]

    def delete_document(self, doc_id: str) -> int:
        return 1
