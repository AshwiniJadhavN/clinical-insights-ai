"""Scenario generation based on contracts, tests, and audit signals."""

from __future__ import annotations

from backend.testing_ai.models import (
    CoverageAnalysisResult,
    CoverageStatus,
    EvidenceItem,
    EvidenceSourceType,
    RiskLevel,
    ScenarioDraft,
)
from backend.testing_ai.prompt_templates import (
    HUMAN_REVIEW_DISCLAIMER,
    SCENARIO_CATALOGUE,
    ScenarioCatalogueItem,
)


class ScenarioGenerator:
    """Generate draft integration scenarios from inferred coverage gaps."""

    def generate(
        self,
        coverage: CoverageAnalysisResult,
        audit_evidence: list[EvidenceItem],
        manual_requirements: list[str],
        target_endpoints: list[str],
        max_scenarios: int,
    ) -> list[ScenarioDraft]:
        prioritized_ids = {
            gap.scenario_id
            for gap in coverage.coverage_gaps
            if gap.status != CoverageStatus.COVERED
        }
        scenarios: list[ScenarioDraft] = []

        for item in SCENARIO_CATALOGUE:
            scenario_id = _scenario_id(str(item["title"]))
            related_endpoints = [str(endpoint) for endpoint in item.get("related_endpoints", [])]
            if target_endpoints and not any(endpoint in target_endpoints for endpoint in related_endpoints):
                continue
            if scenario_id not in prioritized_ids and not self._matches_manual_requirement(item, manual_requirements):
                continue
            evidence = self._build_evidence(item, coverage, audit_evidence)
            scenarios.append(
                ScenarioDraft(
                    scenario_id=scenario_id,
                    title=str(item["title"]),
                    requirement=str(item["requirement"]),
                    system_behavior=str(item["system_behavior"]),
                    risk=str(item["risk"]),
                    risk_level=RiskLevel(item["risk_level"]),
                    expected_result=str(item["expected_result"]),
                    evidence_to_collect=[str(entry) for entry in item["evidence_to_collect"]],
                    related_endpoints=related_endpoints,
                    rationale=self._build_rationale(scenario_id, coverage, manual_requirements),
                    based_on=evidence,
                    human_review_required=True,
                    advisory_message=HUMAN_REVIEW_DISCLAIMER,
                )
            )
            if len(scenarios) >= max_scenarios:
                break

        if scenarios:
            return scenarios

        fallback = SCENARIO_CATALOGUE[0]
        return [
            ScenarioDraft(
                scenario_id=_scenario_id(str(fallback["title"])),
                title=str(fallback["title"]),
                requirement=str(fallback["requirement"]),
                system_behavior=str(fallback["system_behavior"]),
                risk=str(fallback["risk"]),
                risk_level=RiskLevel(fallback["risk_level"]),
                expected_result=str(fallback["expected_result"]),
                evidence_to_collect=[str(entry) for entry in fallback["evidence_to_collect"]],
                related_endpoints=[str(endpoint) for endpoint in fallback.get("related_endpoints", [])],
                rationale="Fallback high-risk scenario selected because no specific gap signals were available.",
                based_on=[
                    EvidenceItem(
                        source_type=EvidenceSourceType.REPORT,
                        source_name="testing-ai",
                        excerpt="Fallback high-risk scenario selected for human review.",
                    )
                ],
                human_review_required=True,
                advisory_message=HUMAN_REVIEW_DISCLAIMER,
            )
        ]

    def _matches_manual_requirement(self, item: ScenarioCatalogueItem, requirements: list[str]) -> bool:
        if not requirements:
            return False
        searchable_text = " ".join(
            [
                str(item["title"]),
                str(item["requirement"]),
                str(item["risk"]),
                " ".join(str(tag) for tag in item["tags"]),
            ]
        ).lower()
        return any(requirement.lower() in searchable_text for requirement in requirements)

    def _build_evidence(
        self,
        item: ScenarioCatalogueItem,
        coverage: CoverageAnalysisResult,
        audit_evidence: list[EvidenceItem],
    ) -> list[EvidenceItem]:
        related_endpoints = item["related_endpoints"]
        evidence: list[EvidenceItem] = []
        for endpoint in coverage.endpoint_contracts:
            if endpoint.path in related_endpoints:
                evidence.append(
                    EvidenceItem(
                        source_type=EvidenceSourceType.ENDPOINT,
                        source_name=endpoint.path,
                        excerpt=f"Methods={','.join(endpoint.methods)} summary={endpoint.summary or 'n/a'}",
                    )
                )
        for gap in coverage.coverage_gaps:
            if gap.scenario_id == _scenario_id(str(item["title"])):
                evidence.append(
                    EvidenceItem(
                        source_type=EvidenceSourceType.REPORT,
                        source_name="coverage_analysis",
                        excerpt=gap.reason,
                    )
                )
                break
        evidence.extend(audit_evidence[:2])
        return evidence or [
            EvidenceItem(
                source_type=EvidenceSourceType.REPORT,
                source_name="coverage_analysis",
                excerpt="Scenario suggested from deterministic risk catalogue.",
            )
        ]

    def _build_rationale(
        self,
        scenario_id: str,
        coverage: CoverageAnalysisResult,
        manual_requirements: list[str],
    ) -> str:
        for gap in coverage.coverage_gaps:
            if gap.scenario_id == scenario_id:
                if manual_requirements:
                    return (
                        f"The scenario maps to a manually requested requirement and current status is {gap.status}."
                    )
                return f"The scenario is prioritized because inferred coverage status is {gap.status}."
        return "The scenario is included as a catalogued high-risk integration check."


def _scenario_id(title: str) -> str:
    return "_".join(title.lower().replace("/", " ").split()).replace("-", "_")