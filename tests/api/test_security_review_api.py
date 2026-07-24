from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend import main as main_module
from backend.config import Settings, get_settings


def _make_app(monkeypatch, tmp_path: Path, **overrides):
    settings = Settings(
        database_url="sqlite:///./data/test.db",
        audit_trail_directory=str(tmp_path),
        **overrides,
    )
    monkeypatch.setattr(main_module, "settings", settings)
    app = main_module.create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    return app


def test_authentication_middleware_blocks_when_api_key_missing(monkeypatch, tmp_path: Path) -> None:
    app = _make_app(monkeypatch, tmp_path, auth_api_key="secret-key")
    client = TestClient(app)

    unauthorized = client.get("/governance/rules")
    authorized = client.get("/governance/rules", headers={"X-API-Key": "secret-key"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_rate_limit_middleware_returns_429_after_threshold(monkeypatch, tmp_path: Path) -> None:
    app = _make_app(monkeypatch, tmp_path, rate_limit_requests=1, rate_limit_window_seconds=60)
    client = TestClient(app)

    first = client.get("/governance/rules")
    second = client.get("/governance/rules")

    assert first.status_code == 200
    assert second.status_code == 429


def test_review_endpoint_records_append_only_decision(monkeypatch, tmp_path: Path) -> None:
    app = _make_app(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/reviews",
        json={
            "query_id": "query-42",
            "reviewer_id": "qa-user",
            "decision": "accepted",
            "comments": "Evidence reviewed and accepted.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["query_id"] == "query-42"
    audit_file = tmp_path / "reviewer_decisions.jsonl"
    assert audit_file.exists()
    assert "human_review_decision" in audit_file.read_text(encoding="utf-8")
