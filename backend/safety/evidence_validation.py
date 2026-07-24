from __future__ import annotations

import re

from backend.rag.retriever import RetrievedChunk
from backend.safety.models import SafetyFinding

_MEASUREMENT_TERMS = ("potassium", "dose", "blood pressure", "bp", "heart rate", "glucose")


class EvidenceValidator:
    def validate(
        self,
        *,
        chunks: list[RetrievedChunk],
        evidence_status: str,
        confidence_score: float,
        confidence_threshold: float,
    ) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []

        if not chunks or evidence_status == "missing":
            findings.append(
                SafetyFinding(
                    code="MISSING_EVIDENCE",
                    requirement_id="SR-003",
                    hazard_id="HAZ-003",
                    message="No retrieved evidence is available to support a medical response.",
                    severity="critical",
                    control_id="RC-001",
                )
            )
            return findings

        if evidence_status != "sufficient" or confidence_score < confidence_threshold:
            findings.append(
                SafetyFinding(
                    code="LOW_CONFIDENCE_RETRIEVAL",
                    requirement_id="SR-004",
                    hazard_id="HAZ-004",
                    message="Retrieved evidence did not meet the configured confidence threshold.",
                    severity="high",
                    control_id="RC-006",
                )
            )

        if any(self._has_corrupted_metadata(chunk) for chunk in chunks):
            findings.append(
                SafetyFinding(
                    code="CORRUPTED_METADATA",
                    requirement_id="SR-009",
                    hazard_id="HAZ-009",
                    message="Retrieved evidence contains corrupted or incomplete citation metadata.",
                    severity="high",
                    control_id="RC-002",
                )
            )

        if self._contains_contradictory_measurements(chunks):
            findings.append(
                SafetyFinding(
                    code="CONTRADICTORY_EVIDENCE",
                    requirement_id="SR-010",
                    hazard_id="HAZ-010",
                    message="Retrieved evidence contains conflicting measurements and requires clarification.",
                    severity="medium",
                    control_id="RC-003",
                )
            )

        return findings

    def _has_corrupted_metadata(self, chunk: RetrievedChunk) -> bool:
        return (
            not chunk.doc_id
            or not chunk.original_filename
            or chunk.chunk_index < 0
            or chunk.similarity_score < 0.0
            or chunk.similarity_score > 1.0
        )

    def _contains_contradictory_measurements(self, chunks: list[RetrievedChunk]) -> bool:
        measurements: dict[str, set[float]] = {}
        for chunk in chunks:
            lowered = chunk.text.lower()
            for term in _MEASUREMENT_TERMS:
                if term not in lowered:
                    continue
                match = re.search(rf"{re.escape(term)}[^0-9]{{0,20}}([0-9]+(?:\.[0-9]+)?)", lowered)
                if not match:
                    continue
                measurements.setdefault(term, set()).add(float(match.group(1)))

        for values in measurements.values():
            if len(values) >= 2 and max(values) - min(values) > 0.5:
                return True
        return False
