import pytest

from backend.config import Settings
from backend.evaluation.scorer import compute_confidence
from backend.rag.chunker import TextChunk
from backend.rag.embedder import FakeEmbedder
from backend.rag.generator import FakeGenerator, GeneratedAnswer
from backend.rag.retriever import FakeRetriever, RetrievedChunk
from backend.safety.decision_engine import SafetyDecisionEngine
from backend.services.query_service import QueryService


def test_evidence_status_missing_when_no_chunks_are_retrieved() -> None:
    result = compute_confidence([], min_threshold=0.6)

    assert result.level == "none"
    assert result.above_threshold == 0


@pytest.mark.asyncio
async def test_evidence_status_sufficient_when_similarity_is_high() -> None:
    retriever = FakeRetriever()
    retriever.index_chunks(
        chunks=[
            TextChunk(
                text="Sample evidence with a strong similarity score for a clinical question.",
                chunk_index=0,
                start_char=0,
                end_char=68,
                doc_id="high-doc",
            )
        ],
        embeddings=[[0.1]],
        original_filename="high.txt",
    )
    service = QueryService(
        settings=Settings(database_url="sqlite:///./data/test.db", confidence_threshold=0.7),
        embedder=FakeEmbedder(),
        retriever=retriever,
        generator=FakeGenerator(),
        safety_engine=SafetyDecisionEngine(confidence_threshold=0.7),
    )

    response = await service.query("What evidence is available?", top_k=1)

    assert response.evidence_status == "sufficient"
    assert response.confidence_score > 0.7


@pytest.mark.asyncio
async def test_evidence_status_weak_when_similarity_is_between_03_and_07() -> None:
    service = QueryService(
        settings=Settings(database_url="sqlite:///./data/test.db", confidence_threshold=0.7),
        embedder=FakeEmbedder(),
        retriever=FixedScoreRetriever(score=0.5),
        generator=FailingGenerator(),
        safety_engine=SafetyDecisionEngine(confidence_threshold=0.7),
    )

    response = await service.query("What evidence is available?", top_k=1)

    assert response.evidence_status == "weak"
    assert response.confidence_score == 0.5
    assert response.model_used == "not-called-insufficient-evidence"


@pytest.mark.asyncio
async def test_llm_is_not_called_when_evidence_is_missing() -> None:
    service = QueryService(
        settings=Settings(database_url="sqlite:///./data/test.db"),
        embedder=FakeEmbedder(),
        retriever=EmptyRetriever(),
        generator=FailingGenerator(),
        safety_engine=SafetyDecisionEngine(confidence_threshold=0.7),
    )

    response = await service.query("What evidence is available?", top_k=1)

    assert response.evidence_status == "missing"
    assert response.retrieved_chunk is None
    assert response.model_used == "not-called-insufficient-evidence"


class FixedScoreRetriever:
    def __init__(self, score: float) -> None:
        self.score = score

    def count(self) -> int:
        return 1

    def index_chunks(self, chunks, embeddings, original_filename: str) -> None:
        return None

    def search(self, query_embedding, top_k: int) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                text="Retrieved text visible in the API response.",
                doc_id="fixed-score-doc",
                chunk_index=0,
                original_filename="fixed.txt",
                similarity_score=self.score,
            )
        ]

    def delete_document(self, doc_id: str) -> int:
        return 0


class EmptyRetriever:
    def count(self) -> int:
        return 0

    def index_chunks(self, chunks, embeddings, original_filename: str) -> None:
        return None

    def search(self, query_embedding, top_k: int) -> list[RetrievedChunk]:
        return []

    def delete_document(self, doc_id: str) -> int:
        return 0


class FailingGenerator:
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        raise AssertionError("Generator should not be called without sufficient evidence.")
