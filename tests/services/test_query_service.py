import pytest

from backend.config import Settings
from backend.rag.chunker import TextChunk
from backend.rag.embedder import FakeEmbedder
from backend.rag.generator import FakeGenerator, GeneratedAnswer
from backend.rag.retriever import FakeRetriever, RetrievedChunk
from backend.schemas.health import SAFETY_DISCLAIMER
from backend.safety.decision_engine import SafetyDecisionEngine
from backend.services.query_service import QueryService


@pytest.mark.asyncio
async def test_query_service_generates_cited_answer_from_indexed_chunks() -> None:
    retriever = FakeRetriever()
    retriever.index_chunks(
        chunks=[
            TextChunk(
                text=(
                    "The trial evaluated a diabetes intervention in adult patients "
                    "and monitored hypoglycemia as a safety outcome."
                ),
                chunk_index=0,
                start_char=0,
                end_char=108,
                doc_id="doc-1",
            )
        ],
        embeddings=[[0.1, 0.2, 0.3]],
        original_filename="sample_trial.txt",
    )
    service = QueryService(
        settings=Settings(database_url="sqlite:///./data/test.db"),
        embedder=FakeEmbedder(),
        retriever=retriever,
        generator=FakeGenerator(),
        safety_engine=SafetyDecisionEngine(confidence_threshold=0.7),
    )

    response = await service.query("What safety outcome was monitored?", top_k=1)

    assert response.answer.startswith("Based on the provided documents")
    assert response.retrieval_count == 1
    assert response.confidence_level == "high"
    assert response.evidence_status == "sufficient"
    assert response.retrieved_chunk is not None
    assert "diabetes intervention" in response.retrieved_chunk
    assert response.citations[0].original_filename == "sample_trial.txt"
    assert response.disclaimer == SAFETY_DISCLAIMER
    assert response.safety_decision == "answer"
    assert response.review_required is False


@pytest.mark.asyncio
async def test_query_service_does_not_generate_when_retrieval_evidence_is_weak() -> None:
    service = QueryService(
        settings=Settings(database_url="sqlite:///./data/test.db", confidence_threshold=0.6),
        embedder=FakeEmbedder(),
        retriever=WeakEvidenceRetriever(),
        generator=FailingGenerator(),
        safety_engine=SafetyDecisionEngine(confidence_threshold=0.6),
    )

    response = await service.query("What safety outcome was monitored?", top_k=1)

    assert response.evidence_status == "weak"
    assert response.confidence_level == "low"
    assert response.model_used == "not-called-insufficient-evidence"
    assert response.citations[0].similarity_score == 0.2
    assert "not strong enough" in response.answer
    assert response.safety_decision == "insufficient_evidence"


@pytest.mark.asyncio
async def test_query_service_returns_refusal_when_generation_times_out(monkeypatch) -> None:
    retriever = FakeRetriever()
    retriever.index_chunks(
        chunks=[
            TextChunk(
                text="Potassium 4.0 mmol/L with clinician verification.",
                chunk_index=0,
                start_char=0,
                end_char=48,
                doc_id="doc-timeout",
            )
        ],
        embeddings=[[0.1, 0.2, 0.3]],
        original_filename="timeout_note.txt",
    )
    service = QueryService(
        settings=Settings(database_url="sqlite:///./data/test.db", llm_timeout_seconds=1),
        embedder=FakeEmbedder(),
        retriever=retriever,
        generator=FakeGenerator(),
        safety_engine=SafetyDecisionEngine(confidence_threshold=0.7),
    )

    async def raise_timeout(awaitable, timeout):
        awaitable.close()
        raise TimeoutError()

    monkeypatch.setattr("backend.services.query_service.asyncio.wait_for", raise_timeout)

    response = await service.query("What was the potassium result?", top_k=1)

    assert response.safety_decision == "refuse"
    assert response.model_used == "not-called-safety-refusal"
    assert response.review_required is True


class WeakEvidenceRetriever:
    def count(self) -> int:
        return 1

    def index_chunks(self, chunks, embeddings, original_filename: str) -> None:
        return None

    def search(self, query_embedding, top_k: int) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                text="Weakly related administrative trial text.",
                doc_id="doc-weak",
                chunk_index=0,
                original_filename="weak.txt",
                similarity_score=0.2,
            )
        ]

    def delete_document(self, doc_id: str) -> int:
        return 0


class FailingGenerator:
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        raise AssertionError("Generator should not be called for weak evidence.")
