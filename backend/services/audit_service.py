"""
Audit service — insert-only query event log.

HIPAA: Only question_length / answer_length are persisted (character counts).
Raw question and answer text are passed in but never stored.
log_query() never raises — a failed DB write must not crash the query pipeline.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from backend.models.audit_log import AuditLogEntry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AuditService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def log_query(
        self,
        *,
        query_id: str,
        question: str,
        answer: str,
        retrieval_count: int,
        confidence_score: float,
        confidence_level: str,
        model_used: str,
        safety_decision: str | None = None,
        refusal_reason: str | None = None,
        correlation_id: str | None = None,
        prompt_version: str | None = None,
        retrieved_doc_ids: list[str] | None = None,
        processing_time_ms: int | None = None,
        review_required: bool = False,
    ) -> None:
        try:
            entry = AuditLogEntry(
                query_id=query_id,
                question_length=len(question),
                answer_length=len(answer),
                retrieval_count=retrieval_count,
                confidence_score=confidence_score,
                confidence_level=confidence_level,
                model_used=model_used,
                safety_decision=safety_decision,
                refusal_reason=refusal_reason,
                correlation_id=correlation_id,
                prompt_version=prompt_version,
                retrieved_doc_ids=",".join(retrieved_doc_ids or []),
                processing_time_ms=processing_time_ms,
                review_required=review_required,
            )
            session = self._factory()
            try:
                session.add(entry)
                session.commit()
            finally:
                session.close()
            logger.info(
                "Audit: query_id=%s logged",
                query_id,
                extra={
                    "query_id": query_id,
                    "correlation_id": correlation_id,
                    "prompt_version": prompt_version,
                    "model_version": model_used,
                    "retrieved_doc_ids": retrieved_doc_ids,
                    "confidence_score": confidence_score,
                    "safety_decision": safety_decision,
                    "refusal_reason": refusal_reason,
                    "processing_time_ms": processing_time_ms,
                    "review_required": review_required,
                },
            )
        except Exception as exc:
            logger.error("Audit write failed: %s", type(exc).__name__)

    def get_recent(self, limit: int = 50) -> list[AuditLogEntry]:
        try:
            session = self._factory()
            try:
                return (
                    session.query(AuditLogEntry)
                    .order_by(AuditLogEntry.created_at.desc())
                    .limit(limit)
                    .all()
                )
            finally:
                session.close()
        except Exception as exc:
            logger.error("Audit read failed: %s", type(exc).__name__)
            return []
