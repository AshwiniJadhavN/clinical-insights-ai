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
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped
from sqlalchemy.types import UserDefinedType

from backend.database.session import Base


class Vector384(UserDefinedType):
    """PostgreSQL pgvector type with a text fallback for local SQLite tests."""

    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        return "VECTOR(384)"


@compiles(Vector384, "sqlite")
def _compile_vector_for_sqlite(type_, compiler, **kw) -> str:
    return "TEXT"


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
    embedding: Mapped[str | None] = Column(Vector384(), nullable=True)
    uploaded_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    processed_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)
