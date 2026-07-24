from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.testing_ai.routes import get_testing_ai_service
from backend.testing_ai.services import TestingAIService


def _override_service(tmp_path: Path) -> TestingAIService:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_health_api.py").write_text(
        "def test_health_signal() -> None:\n"
        "    assert '/health'\n",
        encoding="utf-8",
    )
    audit_dir = tmp_path / "backend/audit/trail"
    audit_dir.mkdir(parents=True)
    return TestingAIService(
        project_root=tmp_path,
        audit_trail_directory=audit_dir,
        generated_tests_directory=tmp_path / "tests/generated",
        report_directory=tmp_path / "docs/testing",
    )


def test_generate_scenarios_endpoint(tmp_path: Path) -> None:
    app.dependency_overrides[get_testing_ai_service] = lambda: _override_service(tmp_path)
    response = TestClient(app).post("/testing-ai/generate-scenarios", json={"max_scenarios": 2})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["human_review_required"] is True


def test_generate_tests_endpoint(tmp_path: Path) -> None:
    app.dependency_overrides[get_testing_ai_service] = lambda: _override_service(tmp_path)
    response = TestClient(app).post("/testing-ai/generate-tests", json={})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["generated_files"]


def test_analyze_failure_endpoint(tmp_path: Path) -> None:
    app.dependency_overrides[get_testing_ai_service] = lambda: _override_service(tmp_path)
    response = TestClient(app).post(
        "/testing-ai/analyze-failure",
        json={"pytest_output": "ValidationError: field required", "github_actions_log": "step failed"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["confidence_score"] >= 0.45


def test_map_risk_endpoint(tmp_path: Path) -> None:
    app.dependency_overrides[get_testing_ai_service] = lambda: _override_service(tmp_path)
    response = TestClient(app).post(
        "/testing-ai/map-risk",
        json={"requirements": ["prompt injection"]},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["mappings"]


def test_report_endpoint(tmp_path: Path) -> None:
    app.dependency_overrides[get_testing_ai_service] = lambda: _override_service(tmp_path)
    response = TestClient(app).get("/testing-ai/report")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["report_path"].endswith("docs/testing/ai_assisted_integration_report.md")
    assert response.json()["graph_path"].endswith("docs/testing/integration_test_graph.mmd")
    assert response.json()["integration_test_graph"].startswith("flowchart TD")
    assert response.json()["coverage"]["risk_coverage_scores"]