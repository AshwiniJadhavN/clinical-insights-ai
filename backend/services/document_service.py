"""
Document service: orchestrates the full document processing pipeline.

Pipeline:
  1. Validate and save file to disk
  2. Parse text (PDF/TXT) → ParsedDocument
  3. Chunk text          → list[TextChunk]
  4. Embed chunks        → list[EmbeddingVector]  (requires embedder)
  5. Index in ChromaDB   → searchable             (requires retriever)
  6. Persist metadata    → Document ORM (DB) | JSON fallback

Metadata storage:
  Primary : PostgreSQL via Document ORM (when session_factory is provided)
  Fallback : data/documents.json (when DB is unavailable in local dev)

Dependency injection:
  EmbedderProtocol, RetrieverProtocol, and sessionmaker are all injected
  via FastAPI Depends() — FakeEmbedder + FakeRetriever + SQLite in tests.

HIPAA:
  - Content is never logged at any level
  - Log only: doc_id (UUID), byte/chunk/index counts, status
  - scrub() wraps all exception messages before logging
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import UploadFile

from backend.config import Settings
from backend.rag.chunker import TextChunk, chunk_text
from backend.rag.embedder import EmbedderProtocol
from backend.rag.retriever import RetrieverProtocol
from backend.schemas.document import DocumentInfo
from backend.utils.file_utils import (
    ensure_directory,
    make_upload_path,
    sanitize_filename,
    validate_upload,
)
from backend.utils.logger import get_logger
from backend.utils.pdf_parser import DocumentParseError, parse_document
from backend.utils.phi_filter import scrub

logger = get_logger(__name__)

_METADATA_FILE = Path("data/documents.json")  # fallback when DB unavailable


class DocumentService:
    """Manages the full lifecycle of uploaded clinical documents."""

    def __init__(
        self,
        settings: Settings,
        embedder: EmbedderProtocol | None = None,
        retriever: RetrieverProtocol | None = None,
        session_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.settings = settings
        self._embedder = embedder
        self._retriever = retriever
        self._session_factory = session_factory
        self._upload_dir = ensure_directory(settings.upload_directory)
        if not session_factory:
            _METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    async def upload(self, file: UploadFile) -> DocumentInfo:
        """
        Run the full upload → parse → chunk → embed → index pipeline.

        Production note: embedding and indexing would be offloaded to a
        background task queue (ARQ/Celery) in a high-throughput system.
        Here they run synchronously for simplicity.
        """
        content = await file.read()
        original_name = file.filename or "document"

        validate_upload(original_name, len(content), self.settings)

        safe_name = sanitize_filename(original_name)
        doc_id, disk_path = make_upload_path(safe_name, self.settings.upload_directory)
        disk_path.write_bytes(content)
        logger.info("Saved: id=%s bytes=%d", doc_id, len(content))

        text_length, chunks, parse_warnings, status, error_message = (
            self._run_extraction(doc_id, disk_path)
        )

        if status != "error" and chunks and self._embedder and self._retriever:
            status, error_message = self._run_indexing(doc_id, original_name, chunks)

        doc = DocumentInfo(
            id=doc_id,
            filename=disk_path.name,
            original_filename=original_name,
            file_type=disk_path.suffix.lstrip("."),
            size_bytes=len(content),
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            status=status,
            text_length=text_length,
            chunk_count=len(chunks),
            parse_warnings=parse_warnings,
            error_message=error_message,
        )
        self._write_record(doc)
        return doc

    def list_documents(self) -> list[DocumentInfo]:
        """Return all documents sorted newest-first."""
        if self._session_factory:
            return self._list_from_db()
        records = self._load_json()
        docs = [DocumentInfo(**v) for v in records.values()]
        return sorted(docs, key=lambda d: d.uploaded_at, reverse=True)

    def get_document(self, doc_id: str) -> DocumentInfo | None:
        if self._session_factory:
            return self._get_from_db(doc_id)
        raw = self._load_json().get(doc_id)
        return DocumentInfo(**raw) if raw else None

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove the file from disk, its entries from ChromaDB, and its DB record.
        Returns True if found and deleted.
        """
        existing = self.get_document(doc_id)
        if not existing:
            return False

        disk_path = self._upload_dir / existing.filename
        if disk_path.exists():
            disk_path.unlink()

        if self._retriever:
            removed = self._retriever.delete_document(doc_id)
            logger.info("Deindexed: id=%s chunks_removed=%d", doc_id, removed)

        if self._session_factory:
            self._delete_from_db(doc_id)
        else:
            records = self._load_json()
            if doc_id in records:
                del records[doc_id]
                self._save_json(records)

        logger.info("Deleted: id=%s", doc_id)
        return True

    # ------------------------------------------------------------------ #
    # Private: extraction pipeline                                         #
    # ------------------------------------------------------------------ #

    def _run_extraction(
        self, doc_id: str, disk_path: Path
    ) -> tuple[int, list[TextChunk], list[str], str, str | None]:
        try:
            parsed = parse_document(disk_path)
            if parsed.is_empty:
                return (
                    0, [], parsed.warnings + ["No text extracted."], "error",
                    "Text extraction produced no usable content.",
                )
            chunks = chunk_text(
                text=parsed.text,
                doc_id=doc_id,
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            )
            logger.info("Extracted: id=%s chars=%d chunks=%d",
                        doc_id, parsed.char_count, len(chunks))
            return parsed.char_count, chunks, parsed.warnings, "ready", None

        except DocumentParseError as exc:
            logger.warning("Parse failed: id=%s reason=%s", doc_id, scrub(str(exc)))
            return 0, [], [], "error", "Document could not be parsed."

    # ------------------------------------------------------------------ #
    # Private: indexing pipeline                                           #
    # ------------------------------------------------------------------ #

    def _run_indexing(
        self, doc_id: str, original_name: str, chunks: list[TextChunk]
    ) -> tuple[str, str | None]:
        assert self._embedder is not None
        assert self._retriever is not None
        try:
            texts = [c.text for c in chunks]
            embeddings = self._embedder.embed_batch(texts)
            self._retriever.index_chunks(chunks, embeddings, original_name)
            logger.info("Indexed: id=%s chunks=%d model=%s",
                        doc_id, len(chunks), self._embedder.model_name)
            return "indexed", None
        except Exception as exc:
            logger.warning("Indexing failed: id=%s reason=%s", doc_id, scrub(str(exc)))
            return "ready", "Indexing failed; document parsed but not searchable yet."

    # ------------------------------------------------------------------ #
    # Private: DB storage (primary)                                        #
    # ------------------------------------------------------------------ #

    def _write_record(self, doc: DocumentInfo) -> None:
        if self._session_factory:
            self._write_to_db(doc)
        else:
            self._write_to_json(doc)

    def _write_to_db(self, doc: DocumentInfo) -> None:
        from backend.models.document import Document
        session = self._new_session()
        try:
            db_doc = Document(
                id=doc.id,
                original_filename=doc.original_filename,
                stored_filename=doc.filename,
                file_size_bytes=doc.size_bytes,
                chunk_count=doc.chunk_count,
                status=doc.status,
                error_message=doc.error_message,
            )
            session.add(db_doc)
            session.commit()
            logger.info("DB record created: id=%s status=%s", doc.id, doc.status)
        except Exception as exc:
            session.rollback()
            logger.warning("DB write failed: id=%s reason=%s", doc.id, scrub(str(exc)))
        finally:
            session.close()

    def _list_from_db(self) -> list[DocumentInfo]:
        from backend.models.document import Document
        session = self._new_session()
        try:
            docs = (
                session.query(Document)
                .order_by(Document.uploaded_at.desc())
                .all()
            )
            return [self._orm_to_schema(d) for d in docs]
        finally:
            session.close()

    def _get_from_db(self, doc_id: str) -> DocumentInfo | None:
        from backend.models.document import Document
        session = self._new_session()
        try:
            db_doc = session.get(Document, doc_id)
            return self._orm_to_schema(db_doc) if db_doc else None
        finally:
            session.close()

    def _delete_from_db(self, doc_id: str) -> None:
        from backend.models.document import Document
        session = self._new_session()
        try:
            db_doc = session.get(Document, doc_id)
            if db_doc:
                session.delete(db_doc)
                session.commit()
        except Exception as exc:
            session.rollback()
            logger.warning("DB delete failed: id=%s reason=%s", doc_id, scrub(str(exc)))
        finally:
            session.close()

    def _new_session(self) -> Any:
        if self._session_factory is None:
            raise RuntimeError("DocumentService session factory is not configured.")
        return self._session_factory()

    def _orm_to_schema(self, db_doc: Any) -> DocumentInfo:
        return DocumentInfo(
            id=db_doc.id,
            filename=db_doc.stored_filename,
            original_filename=db_doc.original_filename,
            file_type=Path(db_doc.stored_filename).suffix.lstrip("."),
            size_bytes=db_doc.file_size_bytes,
            uploaded_at=(
                db_doc.uploaded_at.isoformat() if db_doc.uploaded_at else ""
            ),
            status=db_doc.status,
            chunk_count=db_doc.chunk_count or 0,
            error_message=db_doc.error_message,
        )

    # ------------------------------------------------------------------ #
    # Private: JSON fallback storage (no DB)                              #
    # ------------------------------------------------------------------ #

    def _load_json(self) -> dict[str, dict]:
        if not _METADATA_FILE.exists():
            return {}
        try:
            return json.loads(_METADATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Metadata unreadable (%s) — starting fresh.", type(exc).__name__)
            return {}

    def _save_json(self, records: dict[str, dict]) -> None:
        _METADATA_FILE.write_text(
            json.dumps(records, indent=2, default=str), encoding="utf-8"
        )

    def _write_to_json(self, doc: DocumentInfo) -> None:
        records = self._load_json()
        records[doc.id] = doc.model_dump()
        self._save_json(records)
