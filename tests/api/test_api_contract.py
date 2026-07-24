from fastapi.testclient import TestClient

from backend.main import app


def test_openapi_contract_exposes_core_paths() -> None:
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/health/live" in paths
    assert "/health/ready" in paths
    assert "/metrics" in paths
    assert "/audit/search" in paths
    assert "/ask" in paths
    assert "/query" in paths
    assert "/reviews" in paths
    assert "/documents/upload" in paths
    assert "/advisory/draft" in paths
    assert "/testing-ai/generate-scenarios" in paths
    assert "/testing-ai/generate-tests" in paths
    assert "/testing-ai/analyze-failure" in paths
    assert "/testing-ai/map-risk" in paths
    assert "/testing-ai/report" in paths
    assert "/agentic/draft" not in paths
    assert "/governance/rules" in paths
