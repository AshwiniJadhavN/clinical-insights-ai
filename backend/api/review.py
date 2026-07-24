from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends

from backend.config import Settings, get_settings
from backend.schemas.review import ReviewDecisionRequest, ReviewDecisionResponse
from backend.services.review_service import ReviewDecisionService

router = APIRouter()


def get_review_service(settings: Settings = Depends(get_settings)) -> ReviewDecisionService:
    audit_file = Path(settings.audit_trail_directory) / "reviewer_decisions.jsonl"
    return ReviewDecisionService(audit_file=audit_file)


@router.post(
    "",
    response_model=ReviewDecisionResponse,
    status_code=201,
    summary="Record human review decision",
    description="Store reviewer acceptance, modification, or rejection decisions in an append-only audit file.",
)
async def record_review_decision(
    body: ReviewDecisionRequest,
    service: ReviewDecisionService = Depends(get_review_service),
) -> ReviewDecisionResponse:
    return service.record_decision(body)