from backend.rag.generator import Citation
from backend.rag.retriever import RetrievedChunk
from backend.safety.decision_engine import SafetyDecisionEngine


def test_evidence_validation_returns_insufficient_evidence_for_empty_retrieval() -> None:
    engine = SafetyDecisionEngine(confidence_threshold=0.7)

    decision = engine.evaluate_evidence(
        chunks=[],
        evidence_status="missing",
        confidence_score=0.0,
        confidence_level="none",
    )

    assert decision.action == "insufficient_evidence"
    assert decision.review_required is True


def test_evidence_validation_requests_clarification_for_contradictory_documents() -> None:
    engine = SafetyDecisionEngine(confidence_threshold=0.7)
    chunks = [
        RetrievedChunk(
            text="Potassium 3.2 mmol/L was observed during the first measurement.",
            doc_id="doc-a",
            chunk_index=0,
            original_filename="lab_a.txt",
            similarity_score=0.93,
            metadata={"risk_level": "MEDIUM"},
        ),
        RetrievedChunk(
            text="Potassium 5.1 mmol/L was observed during repeat testing.",
            doc_id="doc-b",
            chunk_index=0,
            original_filename="lab_b.txt",
            similarity_score=0.91,
            metadata={"risk_level": "MEDIUM"},
        ),
    ]

    decision = engine.evaluate_evidence(
        chunks=chunks,
        evidence_status="sufficient",
        confidence_score=0.91,
        confidence_level="high",
    )

    assert decision.action == "clarify"


def test_evidence_validation_refuses_corrupted_metadata() -> None:
    engine = SafetyDecisionEngine(confidence_threshold=0.7)
    chunks = [
        RetrievedChunk(
            text="General clinical note with missing metadata.",
            doc_id="",
            chunk_index=0,
            original_filename="",
            similarity_score=0.82,
            metadata={"risk_level": "LOW"},
        )
    ]

    decision = engine.evaluate_evidence(
        chunks=chunks,
        evidence_status="sufficient",
        confidence_score=0.82,
        confidence_level="high",
    )

    assert decision.action == "refuse"


def test_output_validation_refuses_citation_mismatch() -> None:
    engine = SafetyDecisionEngine(confidence_threshold=0.7)
    chunks = [
        RetrievedChunk(
            text="Adult trial participants reported dizziness as an adverse event.",
            doc_id="doc-1",
            chunk_index=0,
            original_filename="trial.txt",
            similarity_score=0.9,
            metadata={"risk_level": "LOW"},
        )
    ]
    citations = [
        Citation(
            doc_id="doc-2",
            original_filename="other.txt",
            chunk_index=3,
            similarity_score=0.88,
            excerpt="Fabricated excerpt",
        )
    ]

    decision = engine.evaluate_output(
        answer="Based on the evidence, dizziness was observed.",
        citations=citations,
        chunks=chunks,
        confidence_level="high",
    )

    assert decision.action == "refuse"
