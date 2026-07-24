"""
Evidence-bound, draft-only advisory automation.

No method here deploys, merges, deletes, or changes production resources. The
service only generates review reports, test drafts, log analyses, CI reports,
documentation drafts, and patch suggestions that require human review.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import ValidationError

from backend.audit.jsonl_writer import JsonlAuditWriter
from backend.schemas.agentic import (
    AgenticAuditEntry,
    AgenticAutomationRequest,
    AgenticAutomationResponse,
    EvidenceReference,
    Recommendation,
    SafetyStatus,
)

INSUFFICIENT_EVIDENCE_MESSAGE = "Insufficient evidence to determine."
AUDIT_FILE = Path("data/agentic_audit.jsonl")
EvidenceSourceType = Literal[
    "pr_diff_line",
    "file",
    "build_log_excerpt",
    "test_failure_output",
    "dockerfile_instruction",
    "ci_config",
    "documentation",
]


class AgenticDevOpsService:
    def __init__(self, audit_file: Path = AUDIT_FILE) -> None:
        self._audit_file = audit_file
        self._audit_file.parent.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        request: AgenticAutomationRequest,
        governance_result: dict[str, Any] | None = None,
    ) -> AgenticAutomationResponse:
        raw_output = self._generate_raw_output(request, governance_result or {})
        response = validate_agentic_output(raw_output, lambda _: self._safe_error_output(request))
        self._write_audit(request, response)
        return response

    def _generate_raw_output(
        self,
        request: AgenticAutomationRequest,
        governance_result: dict[str, Any],
    ) -> dict[str, Any]:
        evidence = _extract_evidence(request.source_name, request.source_text)
        audit_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        governance_warnings = list(governance_result.get("warnings", []))

        if not evidence:
            return {
                "safety_status": SafetyStatus.INSUFFICIENT_EVIDENCE,
                "automation_type": request.automation_type,
                "agent_name": request.agent_name,
                "model_used": request.model_used,
                "approval_status": "draft_needs_human_review",
                "summary": INSUFFICIENT_EVIDENCE_MESSAGE,
                "recommendations": [],
                "governance_warnings": governance_warnings,
                "output_json": {
                    "message": INSUFFICIENT_EVIDENCE_MESSAGE,
                    "governance": governance_result,
                },
                "audit_id": audit_id,
                "created_at": created_at,
            }

        recommendation = Recommendation(
            title=_title_for(request.automation_type),
            confidence_score=_confidence_for(evidence),
            evidence=evidence,
            reasoning_summary=_reasoning_for(request.automation_type),
            suggested_action=_suggested_action_for(request.automation_type),
        )
        return {
            "safety_status": SafetyStatus.NEEDS_HUMAN_REVIEW,
            "automation_type": request.automation_type,
            "agent_name": request.agent_name,
            "model_used": request.model_used,
            "approval_status": "draft_needs_human_review",
            "summary": "Draft recommendation generated from explicit evidence only.",
            "recommendations": [recommendation.model_dump()],
            "governance_warnings": governance_warnings,
            "output_json": {
                "draft": True,
                "needs_human_review": True,
                "automation_type": request.automation_type,
                "evidence_count": len(evidence),
                "governance": governance_result,
            },
            "audit_id": audit_id,
            "created_at": created_at,
        }

    def _safe_error_output(self, request: AgenticAutomationRequest) -> dict[str, Any]:
        return {
            "safety_status": SafetyStatus.INVALID_OUTPUT,
            "automation_type": request.automation_type,
            "agent_name": request.agent_name,
            "model_used": request.model_used,
            "approval_status": "draft_needs_human_review",
            "summary": "AI output failed schema validation and was rejected.",
            "recommendations": [],
            "governance_warnings": [],
            "output_json": {"error": "Malformed or incomplete AI output rejected."},
            "audit_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc),
        }

    def _write_audit(
        self,
        request: AgenticAutomationRequest,
        response: AgenticAutomationResponse,
    ) -> None:
        evidence = [
            item
            for recommendation in response.recommendations
            for item in recommendation.evidence
        ]
        confidence = (
            min(r.confidence_score for r in response.recommendations)
            if response.recommendations
            else 0.0
        )
        entry = AgenticAuditEntry(
            timestamp=response.created_at,
            audit_id=response.audit_id,
            action=f"agentic_{request.automation_type}",
            input_hash=_hash_input(request.source_text),
            agent_name=request.agent_name,
            model_used=request.model_used,
            confidence_score=confidence,
            evidence_references=evidence,
            output_json=response.model_dump(mode="json"),
            approval_status=response.approval_status,
        )
        JsonlAuditWriter(self._audit_file).append(entry.model_dump(mode="json"))


def validate_agentic_output(
    raw_output: dict[str, Any],
    correction_prompt: Callable[[dict[str, Any]], dict[str, Any]],
) -> AgenticAutomationResponse:
    """Validate strict output, retry once, then return a safe invalid response."""
    try:
        return AgenticAutomationResponse.model_validate(raw_output)
    except ValidationError:
        corrected = correction_prompt(raw_output)
    try:
        return AgenticAutomationResponse.model_validate(corrected)
    except ValidationError:
        fallback = dict(corrected)
        fallback["safety_status"] = SafetyStatus.INVALID_OUTPUT
        fallback["recommendations"] = []
        fallback["summary"] = "AI output failed schema validation and was rejected."
        return AgenticAutomationResponse.model_validate(fallback)


def _extract_evidence(source_name: str, source_text: str) -> list[EvidenceReference]:
    evidence: list[EvidenceReference] = []
    for line_number, line in enumerate(source_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        source_type = _source_type_for(source_name, stripped)
        if source_type is None:
            continue
        evidence.append(
            EvidenceReference(
                source_type=source_type,
                source_name=source_name,
                excerpt=stripped[:500],
                line_number=line_number,
            )
        )
        if len(evidence) == 5:
            break
    return evidence


def _source_type_for(source_name: str, line: str) -> EvidenceSourceType | None:
    lower_source = source_name.lower()
    lower_line = line.lower()
    if lower_source.endswith("dockerfile") or line.startswith(("FROM ", "RUN ", "CMD ", "COPY ")):
        return "dockerfile_instruction"
    if lower_source.endswith((".yml", ".yaml")) or "github/workflows" in lower_source:
        return "ci_config"
    if "failed" in lower_line or "error" in lower_line or "assert" in lower_line:
        return "test_failure_output"
    if "step " in lower_line or "build" in lower_line or "warning" in lower_line:
        return "build_log_excerpt"
    if lower_source.endswith(".md"):
        return "documentation"
    if line.startswith(("+", "-")):
        return "pr_diff_line"
    if "." in source_name:
        return "file"
    return None


def _confidence_for(evidence: list[EvidenceReference]) -> float:
    return min(0.95, round(0.55 + (0.08 * len(evidence)), 2))


def _title_for(automation_type: str) -> str:
    return {
        "pr_review": "Draft PR review finding",
        "pytest_test_draft": "Draft pytest coverage suggestion",
        "build_log_analysis": "Draft build log analysis",
        "ci_cd_report": "Draft CI/CD report finding",
        "documentation_update_draft": "Draft documentation update suggestion",
    }[automation_type]


def _reasoning_for(automation_type: str) -> str:
    return (
        "The recommendation is based only on the cited source evidence and is marked "
        f"as a draft for {automation_type}."
    )


def _suggested_action_for(automation_type: str) -> str:
    return {
        "pr_review": "Review the cited diff or file lines before applying any code change.",
        "pytest_test_draft": "Use the cited behavior to draft or update pytest coverage.",
        "build_log_analysis": "Investigate the cited build or test failure output.",
        "ci_cd_report": "Review the cited CI/CD configuration before changing pipeline behavior.",
        "documentation_update_draft": "Review the cited documentation before applying the draft update.",
    }[automation_type]


def _hash_input(source_text: str) -> str:
    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()
