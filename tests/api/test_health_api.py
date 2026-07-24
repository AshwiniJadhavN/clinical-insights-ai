from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.health import SAFETY_DISCLAIMER


def test_health_endpoint_returns_operational_status() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["disclaimer"] == SAFETY_DISCLAIMER
    assert payload["embedder"]["status"] == "not initialized"
    assert payload["vector_store"]["status"] == "not initialized"


def test_request_id_is_returned_to_client() -> None:
    response = TestClient(app).get("/health", headers={"X-Request-ID": "test-request-123"})

    assert response.headers["X-Request-ID"] == "test-request-123"


def test_metrics_endpoint_returns_prometheus_style_metrics() -> None:
    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    assert "clinical_insights_app_info" in response.text
    assert "clinical_insights_indexed_chunks" in response.text
    assert "clinical_insights_http_requests_total" in response.text
