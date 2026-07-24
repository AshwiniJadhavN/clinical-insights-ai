"""
Controlled advisory automation endpoints.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.audit.jsonl_writer import JsonlAuditWriter
from backend.governance.rule_engine import GovernanceRuleEngine
from backend.observability.metrics import record_advisory_refusal
from backend.schemas.agentic import AgenticAutomationRequest, AgenticAutomationResponse
from backend.services.agentic_service import AgenticDevOpsService

router = APIRouter()
AUDIT_FILE = Path("data/agentic_audit.jsonl")


def get_agentic_service() -> AgenticDevOpsService:
    return AgenticDevOpsService()


def get_governance_engine() -> GovernanceRuleEngine:
    return GovernanceRuleEngine()


@router.post(
    "/draft",
    response_model=AgenticAutomationResponse,
    summary="Generate evidence-bound draft automation output",
    description=(
        "Draft-only advisory developer support automation. This endpoint never deploys, "
        "merges, deletes, or modifies production resources."
    ),
)
def create_agentic_draft(
    body: AgenticAutomationRequest,
    service: AgenticDevOpsService = Depends(get_agentic_service),
    governance: GovernanceRuleEngine = Depends(get_governance_engine),
) -> AgenticAutomationResponse:
    governance_result = governance.evaluate(body.model_dump(mode="json"))
    if governance_result.blocked:
        record_advisory_refusal("governance_block")
        audit_id = _write_governance_block_audit(body, governance_result.model_dump())
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Governance rule blocked advisory automation.",
                "audit_id": audit_id,
                **governance_result.model_dump(),
            },
        )

    return service.run(body, governance_result.model_dump())


def _write_governance_block_audit(
    body: AgenticAutomationRequest,
    governance_result: dict,
) -> str:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    audit_id = str(uuid.uuid4())
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_id": audit_id,
        "action": "governance_block",
        "input_hash": hashlib.sha256(body.source_text.encode("utf-8")).hexdigest(),
        "agent_name": body.agent_name,
        "model_used": body.model_used,
        "confidence_score": 0.0,
        "evidence_references": [],
        "output_json": {
            "automation_type": body.automation_type,
            "source_name": body.source_name,
            "governance": governance_result,
        },
        "approval_status": "draft_needs_human_review",
    }
    JsonlAuditWriter(AUDIT_FILE).append(entry)
    return audit_id
