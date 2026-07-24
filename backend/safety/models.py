from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SafetyAction = Literal["answer", "refuse", "clarify", "insufficient_evidence"]
SafetySeverity = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class SafetyFinding:
    code: str
    requirement_id: str
    hazard_id: str
    message: str
    severity: SafetySeverity = "medium"
    control_id: str | None = None


@dataclass(frozen=True)
class SafetyDecision:
    action: SafetyAction
    rationale: str
    refusal_reason: str | None = None
    findings: tuple[SafetyFinding, ...] = field(default_factory=tuple)
    review_required: bool = False
    policy_id: str = "SAFETY_POLICY_V1"
