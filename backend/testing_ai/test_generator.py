"""Pytest template generation for draft-only integration tests."""

from __future__ import annotations

from pathlib import Path
import re

from backend.testing_ai.models import GeneratedTestFile, ScenarioDraft
from backend.testing_ai.prompt_templates import GENERATED_TEST_BANNER, HUMAN_REVIEW_DISCLAIMER


class TestGenerator:
    """Create safe draft pytest files that require human review before use."""

    def generate(
        self,
        scenarios: list[ScenarioDraft],
        output_directory: Path,
        file_prefix: str,
    ) -> list[GeneratedTestFile]:
        output_directory.mkdir(parents=True, exist_ok=True)
        generated_files: list[GeneratedTestFile] = []
        for scenario in scenarios:
            filename = self._build_unique_filename(output_directory, file_prefix, scenario.title)
            content = self._build_file_content(scenario)
            filename.write_text(content, encoding="utf-8")
            generated_files.append(
                GeneratedTestFile(
                    path=str(filename.as_posix()),
                    scenario_id=scenario.scenario_id,
                    title=scenario.title,
                    human_review_required=True,
                    advisory_message=HUMAN_REVIEW_DISCLAIMER,
                )
            )
        return generated_files

    def _build_unique_filename(self, output_directory: Path, file_prefix: str, title: str) -> Path:
        stem = f"{file_prefix}_{_slugify(title)}_template.py"
        candidate = output_directory / stem
        counter = 1
        while candidate.exists():
            candidate = output_directory / f"{file_prefix}_{_slugify(title)}_{counter}_template.py"
            counter += 1
        return candidate

    def _build_file_content(self, scenario: ScenarioDraft) -> str:
        endpoint_hint = scenario.related_endpoints[0] if scenario.related_endpoints else "/query"
        test_name = f"test_{scenario.scenario_id}"
        evidence_lines = "\n".join(
            f"    # Collect evidence: {evidence_item}"
            for evidence_item in scenario.evidence_to_collect
        )
        return (
            f"{GENERATED_TEST_BANNER}\n\n"
            "import pytest\n"
            "from fastapi.testclient import TestClient\n\n"
            "from backend.main import app\n\n\n"
            f"@pytest.mark.skip(reason=\"Human review required before enabling AI-generated draft test.\")\n"
            f"def {test_name}() -> None:\n"
            f"    \"\"\"{scenario.title}.\"\"\"\n"
            f"    # Requirement: {scenario.requirement}\n"
            f"    # Risk: {scenario.risk}\n"
            f"    # Expected result: {scenario.expected_result}\n"
            f"    client = TestClient(app)\n"
            f"    response = client.get(\"{endpoint_hint}\")\n"
            "    # Replace the request above with the correct integration setup for this scenario.\n"
            f"{evidence_lines}\n"
            "    assert response is not None\n"
        )


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")