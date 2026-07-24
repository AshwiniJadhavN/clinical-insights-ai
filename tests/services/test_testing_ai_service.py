from pathlib import Path

from backend.testing_ai.models import FailureAnalysisRequest, GenerateTestsRequest, RiskMapRequest, ScenarioGenerationRequest
from backend.testing_ai.services import TestingAIService


def _service(tmp_path: Path) -> TestingAIService:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_query_flow.py").write_text(
        "from fastapi.testclient import TestClient\n"
        "from backend.main import app\n\n"
        "def test_query_contract() -> None:\n"
        "    response = TestClient(app).get('/health')\n"
        "    assert response.status_code == 200\n",
        encoding="utf-8",
    )
    audit_dir = tmp_path / "backend/audit/trail"
    audit_dir.mkdir(parents=True)
    (audit_dir / "events.jsonl").write_text(
        '{"event":"query_failed","detail":"timeout while writing audit"}\n',
        encoding="utf-8",
    )
    return TestingAIService(
        project_root=tmp_path,
        audit_trail_directory=audit_dir,
        generated_tests_directory=tmp_path / "tests/generated",
        report_directory=tmp_path / "docs/testing",
    )


def test_generate_scenarios_returns_human_review_drafts(tmp_path: Path) -> None:
    service = _service(tmp_path)
    response = service.generate_scenarios(
        ScenarioGenerationRequest(max_scenarios=3),
        app_routes=[],
    )

    assert response.human_review_required is True
    assert response.scenarios
    assert response.approval_status == "draft_needs_human_review"


def test_generate_tests_creates_non_overwriting_draft_files(tmp_path: Path) -> None:
    service = _service(tmp_path)
    scenarios = service.generate_scenarios(ScenarioGenerationRequest(max_scenarios=1), app_routes=[]).scenarios

    first_response = service.generate_tests(GenerateTestsRequest(scenarios=scenarios), app_routes=[])
    second_response = service.generate_tests(GenerateTestsRequest(scenarios=scenarios), app_routes=[])

    assert len(first_response.generated_files) == 1
    assert len(second_response.generated_files) == 1
    assert first_response.generated_files[0].path != second_response.generated_files[0].path


def test_analyze_failure_returns_structured_json(tmp_path: Path) -> None:
    service = _service(tmp_path)
    response = service.analyze_failure(
        FailureAnalysisRequest(
            pytest_output="AssertionError: expected 200 got 503",
            github_actions_log="job failed during pytest",
            application_log="ERROR database timeout",
        )
    )

    assert response.root_cause_summary
    assert response.likely_failing_component
    assert response.supporting_evidence
    assert response.human_review_required is True


def test_map_risk_returns_traceability_chain(tmp_path: Path) -> None:
    service = _service(tmp_path)
    scenarios = service.generate_scenarios(ScenarioGenerationRequest(max_scenarios=2), app_routes=[]).scenarios
    response = service.map_risk(RiskMapRequest(requirements=["evidence"], scenarios=scenarios))

    assert response.mappings
    assert response.mappings[0].evidence_collected


def test_generate_report_writes_markdown(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.generate_tests(GenerateTestsRequest(), app_routes=[])

    response = service.generate_report(app_routes=[])

    assert response.report_path.endswith("docs/testing/ai_assisted_integration_report.md")
    assert response.graph_path.endswith("docs/testing/integration_test_graph.mmd")
    assert "# AI Assisted Integration Testing Report" in response.markdown
    assert "## Risk Coverage Score" in response.markdown
    assert "Document Ingestion" in response.markdown
    assert "```mermaid" in response.markdown
    assert response.integration_test_graph.startswith("flowchart TD")
    assert response.coverage.risk_coverage_scores