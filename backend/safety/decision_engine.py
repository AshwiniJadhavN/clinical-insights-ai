from __future__ import annotations

from backend.rag.generator import Citation
from backend.rag.retriever import RetrievedChunk
from backend.safety.citation_verifier import CitationVerifier
from backend.safety.evidence_validation import EvidenceValidator
from backend.safety.input_sanitizer import InputSanitizer
from backend.safety.models import SafetyDecision, SafetyFinding
from backend.safety.output_validation import OutputValidator
from backend.safety.policy import SafetyPolicyEnforcer
from backend.safety.prompt_injection import PromptInjectionDetector


class SafetyDecisionEngine:
    def __init__(
        self,
        confidence_threshold: float,
        sanitizer: InputSanitizer | None = None,
        injection_detector: PromptInjectionDetector | None = None,
        evidence_validator: EvidenceValidator | None = None,
        citation_verifier: CitationVerifier | None = None,
        output_validator: OutputValidator | None = None,
        policy_enforcer: SafetyPolicyEnforcer | None = None,
    ) -> None:
        self._confidence_threshold = confidence_threshold
        self._sanitizer = sanitizer or InputSanitizer()
        self._injection_detector = injection_detector or PromptInjectionDetector()
        self._evidence_validator = evidence_validator or EvidenceValidator()
        self._citation_verifier = citation_verifier or CitationVerifier()
        self._output_validator = output_validator or OutputValidator()
        self._policy_enforcer = policy_enforcer or SafetyPolicyEnforcer()

    def sanitize_question(self, question: str) -> str:
        return self._sanitizer.sanitize(question)

    def evaluate_input(self, question: str) -> SafetyDecision:
        detection = self._injection_detector.detect(question)
        findings: list[SafetyFinding] = []
        if detection.detected:
            findings.append(
                SafetyFinding(
                    code="PROMPT_INJECTION",
                    requirement_id="SR-006",
                    hazard_id="HAZ-006",
                    message=detection.reason or "Prompt injection patterns were detected.",
                    severity="critical",
                    control_id="RC-005",
                )
            )
        return self._policy_enforcer.decide(findings)

    def evaluate_evidence(
        self,
        *,
        chunks: list[RetrievedChunk],
        evidence_status: str,
        confidence_score: float,
        confidence_level: str,
    ) -> SafetyDecision:
        findings = self._evidence_validator.validate(
            chunks=chunks,
            evidence_status=evidence_status,
            confidence_score=confidence_score,
            confidence_threshold=self._confidence_threshold,
        )
        return self._policy_enforcer.decide(
            findings,
            default_review_required=confidence_level != "high",
        )

    def evaluate_output(
        self,
        *,
        answer: str,
        citations: list[Citation],
        chunks: list[RetrievedChunk],
        confidence_level: str,
    ) -> SafetyDecision:
        findings: list[SafetyFinding] = []
        findings.extend(self._citation_verifier.validate(citations=citations, chunks=chunks))
        findings.extend(self._output_validator.validate(answer=answer, chunks=chunks))
        return self._policy_enforcer.decide(
            findings,
            default_review_required=confidence_level != "high",
        )

    def timeout_decision(self) -> SafetyDecision:
        return self._policy_enforcer.decide(
            [
                SafetyFinding(
                    code="GENERATION_TIMEOUT",
                    requirement_id="SR-008",
                    hazard_id="HAZ-012",
                    message="The language model did not respond within the configured timeout window.",
                    severity="high",
                    control_id="RC-004",
                )
            ]
        )
