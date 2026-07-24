"""
Pydantic schemas for the Documents API.

Status values:
  "uploaded"  — file saved, not yet processed
  "ready"     — text extracted and chunked, NOT yet in vector store
  "indexed"   — fully processed: parsed, chunked, embedded, in ChromaDB
  "error"     — processing failed
"""

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    size_bytes: int
    uploaded_at: str
    status: str
    text_length: int = 0
    chunk_count: int = 0
    parse_warnings: list[str] = []
    error_message: str | None = None


class UploadResponse(BaseModel):
    message: str
    document: DocumentInfo
