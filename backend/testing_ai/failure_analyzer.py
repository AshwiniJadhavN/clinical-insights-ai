"""Structured CI and pytest failure analysis."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.testing_ai.models import EvidenceItem, EvidenceSourceType, FailureAnalysisResponse
from backend.testing_ai.prompt_templates import FAILURE_PATTERNS, HUMAN_REVIEW_DISCLAIMER


class FailureAnalyzer:
    """Heuristic failure analysis for pytest, CI, and application logs."""

    def analyze(
        self,
        pytest_output: str,
        github_actions_log: str,
        application_log: str,
    ) -> FailureAnalysisResponse:
        normalized_inputs = {
            EvidenceSourceType.TEST_FILE: pytest_output,
            EvidenceSourceType.CI_LOG: github_actions_log,
            EvidenceSourceType.APPLICATION_LOG: application_log,
        }
        lower_blob = "\n".join(normalized_inputs.values()).lower()
        matched_pattern = next(
            (pattern for pattern in FAILURE_PATTERNS if str(pattern["pattern"]) in lower_blob),
            None,
        )
        evidence = self._collect_evidence(normalized_inputs)

        if matched_pattern is None:
            return FailureAnalysisResponse(
                root_cause_summary="No strong deterministic signal was found in the provided logs.",
                likely_failing_component="unknown_requires_human_triage",
                confidence_score=0.32,
                suggested_next_debugging_steps=[
                    "Review the first failing pytest traceback and surrounding setup logs.",
                    "Correlate the failure timestamp with application and dependency logs.",
                ],
                possible_fix="Human review is required to identify the failing integration boundary.",
                supporting_evidence=evidence,
                human_review_required=True,
                advisory_message=HUMAN_REVIEW_DISCLAIMER,
                generated_at=datetime.now(timezone.utc),
            )

        score = self._score_confidence(lower_blob, str(matched_pattern["pattern"]))
        return FailureAnalysisResponse(
            root_cause_summary=str(matched_pattern["summary"]),
            likely_failing_component=str(matched_pattern["component"]),
            confidence_score=score,
            suggested_next_debugging_steps=[str(step) for step in matched_pattern["steps"]],
            possible_fix=str(matched_pattern["fix"]),
            supporting_evidence=evidence,
            human_review_required=True,
            advisory_message=HUMAN_REVIEW_DISCLAIMER,
            generated_at=datetime.now(timezone.utc),
        )

    def _collect_evidence(
        self,
        normalized_inputs: dict[EvidenceSourceType, str],
    ) -> list[EvidenceItem]:
        evidence: list[EvidenceItem] = []
        for source_type, text in normalized_inputs.items():
            if not text.strip():
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                lowered = line.lower()
                if any(token in lowered for token in ("error", "failed", "traceback", "timeout", "503", "assert")):
                    evidence.append(
                        EvidenceItem(
                            source_type=source_type,
                            source_name=source_type.value,
                            excerpt=line[:500],
                            line_number=line_number,
                        )
                    )
                if len(evidence) >= 6:
                    return evidence
        if evidence:
            return evidence
        return [
            EvidenceItem(
                source_type=EvidenceSourceType.CI_LOG,
                source_name="combined_logs",
                excerpt="Logs supplied without a recognizable failure signature.",
            )
        ]

    def _score_confidence(self, combined_logs: str, pattern: str) -> float:
        hits = combined_logs.count(pattern)
        return min(0.95, round(0.45 + (0.15 * hits), 2))