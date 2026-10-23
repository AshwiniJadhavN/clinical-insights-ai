from __future__ import annotations

import re

from backend.rag.generator import Citation
from backend.rag.retriever import RetrievedChunk
from backend.safety.models import SafetyFinding


class CitationVerifier:
    def validate(
        self,
        *,
        answer: str,
        citations: list[Citation],
        chunks: list[RetrievedChunk],
    ) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        references = {
            int(value)
            for value in re.findall(r"(?<!\[)\[(\d+)\](?!\])", answer)
        }
        if not references:
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

        invalid_references = sorted(
            reference for reference in references if not 1 <= reference <= len(chunks)
        )
        if invalid_references:
            findings.append(
                SafetyFinding(
                    code="FABRICATED_CITATION",
                    requirement_id="SR-002",
                    hazard_id="HAZ-002",
                    message="Generated output referenced evidence that was not retrieved.",
                    severity="critical",
                    control_id="RC-002",
                )
            )

        cited_by_reference = {
            citation.reference_id: citation
            for citation in citations
            if citation.reference_id is not None
        }
        for reference in references - set(invalid_references):
            citation = cited_by_reference.get(reference)
            expected = chunks[reference - 1]
            if citation is None or (
                citation.doc_id,
                citation.chunk_index,
            ) != (expected.doc_id, expected.chunk_index):
                findings.append(
                    SafetyFinding(
                        code="CITATION_MISMATCH",
                        requirement_id="SR-002",
                        hazard_id="HAZ-008",
                        message="Generated citation marker does not match its retrieved source.",
                        severity="high",
                        control_id="RC-002",
                    )
                )

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
