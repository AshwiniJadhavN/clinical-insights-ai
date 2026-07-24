from __future__ import annotations

from backend.safety.models import SafetyDecision, SafetyFinding

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_REFUSE_CODES = {
    "PROMPT_INJECTION",
    "FABRICATED_CITATION",
    "MISSING_CITATIONS",
    "CITATION_MISMATCH",
    "PROMPT_LEAKAGE",
    "UNSUPPORTED_CONCLUSION",
    "CORRUPTED_METADATA",
    "EMPTY_OUTPUT",
    "GENERATION_TIMEOUT",
}
_CLARIFY_CODES = {"CONTRADICTORY_EVIDENCE"}
_INSUFFICIENT_CODES = {"MISSING_EVIDENCE", "LOW_CONFIDENCE_RETRIEVAL"}


class SafetyPolicyEnforcer:
    def decide(self, findings: list[SafetyFinding], *, default_review_required: bool = False) -> SafetyDecision:
        if not findings:
            return SafetyDecision(
                action="answer",
                rationale="Safety checks passed for input, evidence, citations, and output validation.",
                review_required=default_review_required,
            )

        ordered = tuple(sorted(findings, key=lambda finding: (_SEVERITY_ORDER[finding.severity], finding.code)))
        codes = {finding.code for finding in ordered}
        rationale = "; ".join(finding.message for finding in ordered[:2])

        if codes & _REFUSE_CODES:
            return SafetyDecision(
                action="refuse",
                rationale=rationale,
                refusal_reason=rationale,
                findings=ordered,
                review_required=True,
            )
        if codes & _CLARIFY_CODES:
            return SafetyDecision(
                action="clarify",
                rationale=rationale,
                refusal_reason=rationale,
                findings=ordered,
                review_required=True,
            )
        if codes & _INSUFFICIENT_CODES:
            return SafetyDecision(
                action="insufficient_evidence",
                rationale=rationale,
                refusal_reason=rationale,
                findings=ordered,
                review_required=True,
            )

        return SafetyDecision(
            action="refuse",
            rationale=rationale,
            refusal_reason=rationale,
            findings=ordered,
            review_required=True,
        )
