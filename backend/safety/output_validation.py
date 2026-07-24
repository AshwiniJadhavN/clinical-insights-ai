from __future__ import annotations

import re

from backend.rag.retriever import RetrievedChunk
from backend.safety.models import SafetyFinding

_SYSTEM_LEAK_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [r"system prompt", r"ignore previous instructions", r"developer message"]
]
_UNSUPPORTED_CONCLUSION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"definitive diagnosis",
        r"must start",
        r"immediately prescribe",
        r"certainly indicates",
    ]
]
_TOKEN_PATTERN = re.compile(r"[a-z]{5,}")
_STOPWORDS = {"therefore", "clinical", "patient", "provided", "documents", "evidence", "question"}


class OutputValidator:
    def validate(self, *, answer: str, chunks: list[RetrievedChunk]) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        if not answer.strip():
            findings.append(
                SafetyFinding(
                    code="EMPTY_OUTPUT",
                    requirement_id="SR-011",
                    hazard_id="HAZ-011",
                    message="Generated output was empty and cannot be returned safely.",
                    severity="high",
                    control_id="RC-004",
                )
            )
            return findings

        if any(pattern.search(answer) for pattern in _SYSTEM_LEAK_PATTERNS):
            findings.append(
                SafetyFinding(
                    code="PROMPT_LEAKAGE",
                    requirement_id="SR-007",
                    hazard_id="HAZ-007",
                    message="Generated output attempted to reveal prompt or system control content.",
                    severity="critical",
                    control_id="RC-004",
                )
            )

        if any(pattern.search(answer) for pattern in _UNSUPPORTED_CONCLUSION_PATTERNS) and not self._evidence_supports(answer, chunks):
            findings.append(
                SafetyFinding(
                    code="UNSUPPORTED_CONCLUSION",
                    requirement_id="SR-001",
                    hazard_id="HAZ-001",
                    message="Generated output made a medical conclusion that is not lexically supported by retrieved evidence.",
                    severity="critical",
                    control_id="RC-004",
                )
            )

        return findings

    def _evidence_supports(self, answer: str, chunks: list[RetrievedChunk]) -> bool:
        answer_tokens = {token for token in _TOKEN_PATTERN.findall(answer.lower()) if token not in _STOPWORDS}
        evidence_tokens = {
            token
            for chunk in chunks
            for token in _TOKEN_PATTERN.findall(chunk.text.lower())
            if token not in _STOPWORDS
        }
        if not answer_tokens:
            return True
        overlap = len(answer_tokens & evidence_tokens) / len(answer_tokens)
        return overlap >= 0.2
