"""Requirement-to-test traceability mapping."""

from __future__ import annotations

from backend.testing_ai.models import RiskLevel, RiskMapEntry, ScenarioDraft
from backend.testing_ai.prompt_templates import SCENARIO_CATALOGUE


class RiskMapper:
    """Map requirements to behavior, risk, tests, and expected evidence."""

    def map(self, requirements: list[str], scenarios: list[ScenarioDraft]) -> list[RiskMapEntry]:
        if scenarios:
            mappings = self._map_from_scenarios(requirements, scenarios)
        else:
            mappings = self._map_from_catalogue(requirements)

        return mappings or [
            RiskMapEntry(
                requirement=requirements[0] if requirements else "Manual review required",
                system_behavior="No deterministic mapping could be inferred from the current catalogue.",
                risk="Traceability is incomplete until a reviewer selects an appropriate integration scenario.",
                integration_test="Human-authored integration test required",
                expected_result="Reviewer identifies the intended system behavior and expected evidence.",
                evidence_collected=["review notes", "requirements clarification"],
                risk_level=RiskLevel.MEDIUM,
                related_endpoints=[],
                human_review_required=True,
            )
        ]

    def _map_from_scenarios(
        self,
        requirements: list[str],
        scenarios: list[ScenarioDraft],
    ) -> list[RiskMapEntry]:
        mappings: list[RiskMapEntry] = []
        for scenario in scenarios:
            if requirements and not any(_matches_requirement(scenario, requirement) for requirement in requirements):
                continue
            mappings.append(
                RiskMapEntry(
                    requirement=scenario.requirement,
                    system_behavior=scenario.system_behavior,
                    risk=scenario.risk,
                    integration_test=scenario.title,
                    expected_result=scenario.expected_result,
                    evidence_collected=scenario.evidence_to_collect,
                    risk_level=scenario.risk_level,
                    related_endpoints=scenario.related_endpoints,
                    human_review_required=True,
                )
            )
        return mappings

    def _map_from_catalogue(self, requirements: list[str]) -> list[RiskMapEntry]:
        mappings: list[RiskMapEntry] = []
        for item in SCENARIO_CATALOGUE:
            searchable_text = " ".join(
                [
                    str(item["title"]),
                    str(item["requirement"]),
                    str(item["system_behavior"]),
                    str(item["risk"]),
                ]
            ).lower()
            if requirements and not any(requirement.lower() in searchable_text for requirement in requirements):
                continue
            mappings.append(
                RiskMapEntry(
                    requirement=str(item["requirement"]),
                    system_behavior=str(item["system_behavior"]),
                    risk=str(item["risk"]),
                    integration_test=str(item["title"]),
                    expected_result=str(item["expected_result"]),
                    evidence_collected=[str(entry) for entry in item["evidence_to_collect"]],
                    risk_level=RiskLevel(item["risk_level"]),
                    related_endpoints=[str(endpoint) for endpoint in item.get("related_endpoints", [])],
                    human_review_required=True,
                )
            )
        return mappings


def _matches_requirement(scenario: ScenarioDraft, requirement: str) -> bool:
    haystack = " ".join(
        [
            scenario.title,
            scenario.requirement,
            scenario.system_behavior,
            scenario.risk,
        ]
    ).lower()
    return requirement.lower() in haystack