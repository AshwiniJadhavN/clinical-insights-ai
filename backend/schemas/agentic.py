"""
Strict schemas for controlled advisory automation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SafetyStatus(str, Enum):
    SAFE_TO_REVIEW = "SAFE_TO_REVIEW"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_OUTPUT = "INVALID_OUTPUT"


AutomationType = Literal[
    "pr_review",
    "pytest_test_draft",
    "build_log_analysis",
    "ci_cd_report",
    "documentation_update_draft",
]


class EvidenceReference(BaseModel):
    source_type: Literal[
        "pr_diff_line",
        "file",
        "build_log_excerpt",
        "test_failure_output",
        "dockerfile_instruction",
        "ci_config",
        "documentation",
    ]
    source_name: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    line_number: int | None = Field(default=None, ge=1)


class Recommendation(BaseModel):
    title: str = Field(min_length=1)
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceReference] = Field(min_length=1)
    reasoning_summary: str = Field(min_length=1)
    suggested_action: str = Field(min_length=1)


class AgenticAutomationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    automation_type: AutomationType
    agent_name: str = Field(min_length=1)
    source_name: str = ""
    source_text: str = Field(min_length=1)
    model_used: str = "deterministic-devops-agent-v1"


class AgenticAutomationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    safety_status: SafetyStatus
    automation_type: AutomationType
    agent_name: str
    model_used: str
    approval_status: Literal["draft_needs_human_review"]
    summary: str
    recommendations: list[Recommendation]
    governance_warnings: list[str] = []
    output_json: dict[str, Any]
    audit_id: str
    created_at: datetime


class AgenticAuditEntry(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    timestamp: datetime
    audit_id: str
    action: str
    input_hash: str
    agent_name: str
    model_used: str
    confidence_score: float
    evidence_references: list[EvidenceReference]
    output_json: dict[str, Any]
    approval_status: Literal["draft_needs_human_review"]
