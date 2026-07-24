"""
Audit log API router — GET /audit.

Returns recent query audit entries for the Audit Log UI tab.
Gracefully returns an empty list when the database is not initialized
(e.g. local dev without PostgreSQL running).

api-design conventions:
  GET /audit       — read-only, no request body
  status 200       — always; empty list when DB unavailable, not a 503
  ?limit=N         — cap at 200 records per response
"""

from fastapi import APIRouter, Depends, Query

from backend.schemas.audit import AuditEntryResponse
from backend.services.audit_service import AuditService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _get_audit_service_optional() -> AuditService | None:
    try:
        from backend.database.session import get_session_factory
        return AuditService(get_session_factory())
    except RuntimeError:
        return None


@router.get(
    "",
    response_model=list[AuditEntryResponse],
    status_code=200,
    summary="List audit log entries",
    description="Return recent RAG query events. Question/answer text is never stored.",
)
def list_audit_entries(
    limit: int = Query(default=50, ge=1, le=200),
    service: AuditService | None = Depends(_get_audit_service_optional),
) -> list[AuditEntryResponse]:
    if service is None:
        return []
    entries = service.get_recent(limit=limit)
    return [AuditEntryResponse.model_validate(e) for e in entries]
