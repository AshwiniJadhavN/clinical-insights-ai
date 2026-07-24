"""
Documents API router.

HTTP concerns only: parse request, call service, return response.
No business logic. No direct file I/O. No DB access.

api-design skill applied:
  - Plural nouns in URLs (/documents/)
  - Correct status codes: 201 Created, 204 No Content, 422 Unprocessable
  - Dependency injection via Depends (never inline instantiation)
  - Generic error messages only (no internal detail in 4xx/5xx)
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.config import Settings, get_settings
from backend.rag.embedder import EmbedderProtocol
from backend.rag.retriever import RetrieverProtocol
from backend.schemas.document import DocumentInfo, UploadResponse
from backend.services.document_service import DocumentService

router = APIRouter()


def _get_embedder_or_none() -> EmbedderProtocol | None:
    try:
        from backend.rag.embedder import get_embedder
        return get_embedder()
    except RuntimeError:
        return None


def _get_retriever_or_none() -> RetrieverProtocol | None:
    try:
        from backend.retrieval.sync import get_sync_retriever
        return get_sync_retriever()
    except RuntimeError:
        pass
    try:
        from backend.rag.retriever import get_retriever
        return get_retriever()
    except RuntimeError:
        return None


def get_document_service(
    settings: Settings = Depends(get_settings),
) -> DocumentService:
    """
    FastAPI dependency: provides a fully-wired DocumentService.

    Resolves embedder and retriever from their module-level singletons.
    Resolves session_factory from the DB singleton (gracefully None if
    the DB is not yet initialized, e.g. in local dev without PostgreSQL).
    """
    session_factory = None
    try:
        from backend.database.session import get_session_factory
        session_factory = get_session_factory()
    except RuntimeError:
        pass

    return DocumentService(
        settings=settings,
        embedder=_get_embedder_or_none(),
        retriever=_get_retriever_or_none(),
        session_factory=session_factory,
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a clinical document",
    description="Accepts PDF or TXT files. Parses, chunks, embeds, and indexes for semantic search.",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT file"),
    service: DocumentService = Depends(get_document_service),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=422, detail="Filename is required.")
    try:
        doc = await service.upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return UploadResponse(message="Document uploaded successfully.", document=doc)


@router.get(
    "/",
    response_model=list[DocumentInfo],
    summary="List all uploaded documents",
)
def list_documents(
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentInfo]:
    return service.list_documents()


@router.delete(
    "/{document_id}",
    status_code=204,
    summary="Delete a document",
)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete file from disk, remove from vector index, clear DB record."""
    if not service.delete_document(document_id):
        raise HTTPException(
            status_code=404, detail=f"Document '{document_id}' not found."
        )
