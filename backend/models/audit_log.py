"""
Audit log ORM model.

Insert-only — no UPDATE or DELETE operations ever performed on this table.

HIPAA:
  question_length / answer_length store character counts only, not the text.
  query_id is an opaque UUID.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped

from backend.database.session import Base


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id: Mapped[str] = Column(String, nullable=False, index=True)
    question_length: Mapped[int] = Column(Integer, nullable=False)
    answer_length: Mapped[int] = Column(Integer, nullable=False)
    retrieval_count: Mapped[int] = Column(Integer, nullable=False)
    confidence_score: Mapped[float] = Column(Float, nullable=False)
    confidence_level: Mapped[str] = Column(String(10), nullable=False)
    model_used: Mapped[str] = Column(String, nullable=False)
    safety_decision: Mapped[str | None] = Column(String(32), nullable=True)
    refusal_reason: Mapped[str | None] = Column(String, nullable=True)
    correlation_id: Mapped[str | None] = Column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = Column(String(64), nullable=True)
    retrieved_doc_ids: Mapped[str | None] = Column(String, nullable=True)
    processing_time_ms: Mapped[int | None] = Column(Integer, nullable=True)
    review_required: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
