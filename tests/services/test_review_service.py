from pathlib import Path

from backend.schemas.review import ReviewDecisionRequest
from backend.services.review_service import ReviewDecisionService


def test_review_service_records_reviewer_decision(tmp_path: Path) -> None:
    audit_file = tmp_path / "reviewer_decisions.jsonl"
    service = ReviewDecisionService(audit_file=audit_file)

    response = service.record_decision(
        ReviewDecisionRequest(
            query_id="query-123",
            reviewer_id="reviewer-a",
            decision="modified",
            modified_answer="Clinician-modified answer.",
            comments="Adjusted wording for clarity.",
        )
    )

    assert response.query_id == "query-123"
    assert response.decision == "modified"
    assert audit_file.exists()
    contents = audit_file.read_text(encoding="utf-8")
    assert "human_review_decision" in contents