"""
Document ORM model.

Tracks every uploaded clinical document through its processing lifecycle.

Status lifecycle: "processing" → "ready" | "error"

HIPAA:
    The table stores metadata and may store chunk content/embeddings for
    retrieval workflows. Uploaded source file bytes live on the configured
    upload path and are not stored as binary blobs in this table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped

from backend.database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = Column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    original_filename: Mapped[str] = Column(String(255), nullable=False)
    stored_filename: Mapped[str] = Column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = Column(Integer, nullable=False)
    chunk_count: Mapped[int] = Column(Integer, default=0, nullable=False)
    # "processing" → "ready" | "error"
    status: Mapped[str] = Column(String(20), default="processing", nullable=False)
    error_message: Mapped[str | None] = Column(String(500), nullable=True)
    content_text: Mapped[str | None] = Column(Text, nullable=True)
    risk_level: Mapped[str] = Column(String(20), default="LOW", nullable=False)
    # pgvector migration stores this as vector(384); SQLAlchemy keeps a string
    # literal here to avoid a runtime dependency on pgvector-python.
    embedding: Mapped[str | None] = Column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    processed_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)
