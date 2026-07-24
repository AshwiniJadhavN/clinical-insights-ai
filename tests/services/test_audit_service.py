from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.models.audit_log import AuditLogEntry
from backend.services.audit_service import AuditService


def test_audit_service_persists_safety_metadata() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    service = AuditService(SessionFactory)
    service.log_query(
        query_id="query-1",
        question="What evidence supports this?",
        answer="Insufficient evidence.",
        retrieval_count=0,
        confidence_score=0.0,
        confidence_level="none",
        model_used="not-called-insufficient-evidence",
        safety_decision="insufficient_evidence",
        refusal_reason="No retrieved evidence is available to support a medical response.",
        correlation_id="corr-1",
        prompt_version="clinical-rag-safety-v1",
        retrieved_doc_ids=["doc-1", "doc-2"],
        processing_time_ms=123,
        review_required=True,
    )

    session = SessionFactory()
    try:
        entry = session.query(AuditLogEntry).one()
        assert entry.safety_decision == "insufficient_evidence"
        assert entry.correlation_id == "corr-1"
        assert entry.prompt_version == "clinical-rag-safety-v1"
        assert entry.retrieved_doc_ids == "doc-1,doc-2"
        assert entry.processing_time_ms == 123
        assert entry.review_required is True
    finally:
        session.close()
