"""
QueryLog ORM model.

Append-only table. Records every RAG query for analytics and debugging.

HIPAA:
  question_length and answer_length store character counts only.
  No question text, no answer text, no patient identifiers.
  query_id is omitted here (see audit_log for the separate HIPAA audit trail).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped

from backend.database.session import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[str] = Column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    question_length: Mapped[int] = Column(Integer, nullable=False)
    answer_length: Mapped[int] = Column(Integer, nullable=False)
    retrieval_count: Mapped[int] = Column(Integer, nullable=False)
    confidence_score: Mapped[float] = Column(Float, nullable=False)
    confidence_level: Mapped[str] = Column(String(20), nullable=False)
    model_used: Mapped[str] = Column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = Column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = Column(Integer, default=0, nullable=False)
    duration_ms: Mapped[int] = Column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
