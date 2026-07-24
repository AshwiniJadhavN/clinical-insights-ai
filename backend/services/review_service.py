from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.audit.jsonl_writer import JsonlAuditWriter
from backend.schemas.review import ReviewDecisionRequest, ReviewDecisionResponse


class ReviewDecisionService:
    def __init__(self, audit_file: Path) -> None:
        self._audit_file = audit_file
        self._writer = JsonlAuditWriter(audit_file)

    def record_decision(self, payload: ReviewDecisionRequest) -> ReviewDecisionResponse:
        created_at = datetime.now(timezone.utc)
        self._writer.append(
            {
                "event_type": "human_review_decision",
                "query_id": payload.query_id,
                "reviewer_id": payload.reviewer_id,
                "decision": payload.decision,
                "modified_answer_length": len(payload.modified_answer or ""),
                "comments_length": len(payload.comments or ""),
                "created_at": created_at.isoformat(),
            }
        )
        return ReviewDecisionResponse(
            query_id=payload.query_id,
            reviewer_id=payload.reviewer_id,
            decision=payload.decision,
            created_at=created_at,
            audit_file=str(self._audit_file),
        )
