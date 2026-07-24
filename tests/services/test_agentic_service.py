from pathlib import Path

from backend.schemas.agentic import AgenticAutomationRequest, SafetyStatus
from backend.services.agentic_service import (
    AgenticDevOpsService,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    validate_agentic_output,
)


def test_agentic_service_generates_evidence_bound_draft_and_audit(tmp_path: Path) -> None:
    audit_file = tmp_path / "agentic_audit.jsonl"
    service = AgenticDevOpsService(audit_file=audit_file)
    request = AgenticAutomationRequest(
        automation_type="pr_review",
        agent_name="Code Review Agent",
        source_name="backend/main.py",
        source_text="+ app.include_router(agentic.router, prefix='/agentic')",
    )

    response = service.run(request)

    assert response.safety_status == SafetyStatus.NEEDS_HUMAN_REVIEW
    assert response.approval_status == "draft_needs_human_review"
    assert response.recommendations[0].confidence_score > 0
    assert response.recommendations[0].evidence[0].source_name == "backend/main.py"
    assert response.recommendations[0].evidence[0].line_number == 1

    audit_lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 1
    assert "Code Review Agent" in audit_lines[0]
    assert "draft_needs_human_review" in audit_lines[0]


def test_agentic_service_returns_insufficient_evidence_without_source_reference(
    tmp_path: Path,
) -> None:
    service = AgenticDevOpsService(audit_file=tmp_path / "agentic_audit.jsonl")
    request = AgenticAutomationRequest(
        automation_type="build_log_analysis",
        agent_name="Build Log Agent",
        source_name="plain-input",
        source_text="No actionable source reference is present.",
    )

    response = service.run(request)

    assert response.safety_status == SafetyStatus.INSUFFICIENT_EVIDENCE
    assert response.summary == INSUFFICIENT_EVIDENCE_MESSAGE
    assert response.recommendations == []


def test_agentic_output_validation_retries_once_then_returns_safe_error() -> None:
    response = validate_agentic_output(
        raw_output={"summary": "malformed"},
        correction_prompt=lambda _: {
            "safety_status": "INVALID_OUTPUT",
            "automation_type": "pr_review",
            "agent_name": "Schema Guard Agent",
            "model_used": "deterministic-devops-agent-v1",
            "approval_status": "draft_needs_human_review",
            "summary": "AI output failed schema validation and was rejected.",
            "recommendations": [],
            "output_json": {"error": "Malformed or incomplete AI output rejected."},
            "audit_id": "audit-id",
            "created_at": "2026-07-06T00:00:00Z",
        },
    )

    assert response.safety_status == SafetyStatus.INVALID_OUTPUT
    assert response.recommendations == []
