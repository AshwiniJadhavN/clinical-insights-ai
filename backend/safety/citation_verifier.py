from __future__ import annotations

from backend.rag.generator import Citation
from backend.rag.retriever import RetrievedChunk
from backend.safety.models import SafetyFinding


class CitationVerifier:
    def validate(
        self,
        *,
        citations: list[Citation],
        chunks: list[RetrievedChunk],
    ) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        if not citations:
            findings.append(
                SafetyFinding(
                    code="MISSING_CITATIONS",
                    requirement_id="SR-002",
                    hazard_id="HAZ-002",
                    message="Generated output did not include citations for the supporting evidence.",
                    severity="critical",
                    control_id="RC-002",
                )
            )
            return findings

        valid_sources = {(chunk.doc_id, chunk.chunk_index): chunk for chunk in chunks}
        for citation in citations:
            source = valid_sources.get((citation.doc_id, citation.chunk_index))
            if source is None:
                findings.append(
                    SafetyFinding(
                        code="FABRICATED_CITATION",
                        requirement_id="SR-002",
                        hazard_id="HAZ-002",
                        message="Generated output referenced a citation that was not present in retrieved evidence.",
                        severity="critical",
                        control_id="RC-002",
                    )
                )
                continue
            excerpt = citation.excerpt.strip()
            if excerpt and excerpt not in source.text:
                findings.append(
                    SafetyFinding(
                        code="CITATION_MISMATCH",
                        requirement_id="SR-002",
                        hazard_id="HAZ-008",
                        message="Generated citation excerpt does not match the retrieved source chunk.",
                        severity="high",
                        control_id="RC-002",
                    )
                )
        return findings
