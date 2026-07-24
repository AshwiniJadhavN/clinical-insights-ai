from fastapi.testclient import TestClient

from backend.main import app


def test_agentic_draft_endpoint_returns_draft_needing_human_review() -> None:
    response = TestClient(app).post(
        "/advisory/draft",
        json={
            "automation_type": "documentation_update_draft",
            "agent_name": "Documentation Agent",
            "source_name": "README.md",
            "source_text": "audit_id: demo-123\n## CI/CD Pipeline Overview\nThe workflow uses gates.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["safety_status"] == "NEEDS_HUMAN_REVIEW"
    assert payload["approval_status"] == "draft_needs_human_review"
    assert payload["recommendations"][0]["evidence"][0]["source_type"] == "documentation"


def test_legacy_agentic_draft_endpoint_remains_compatible() -> None:
    response = TestClient(app).post(
        "/agentic/draft",
        json={
            "automation_type": "documentation_update_draft",
            "agent_name": "Documentation Agent",
            "source_name": "README.md",
            "source_text": "audit_id: demo-legacy\n## CI/CD Pipeline Overview\nThe workflow uses gates.",
        },
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "draft_needs_human_review"


def test_agentic_draft_endpoint_blocks_sensitive_file_governance_violation() -> None:
    response = TestClient(app).post(
        "/advisory/draft",
        json={
            "automation_type": "pr_review",
            "agent_name": "Code Review Gate",
            "source_name": "deploy/private.pem",
            "source_text": "audit_id: demo-456\n+ secret material",
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["blocked"] is True
    assert "block_sensitive_files" in detail["rule_triggered"]
    assert detail["audit_id"]


def test_agentic_draft_endpoint_includes_non_blocking_governance_warnings() -> None:
    response = TestClient(app).post(
        "/advisory/draft",
        json={
            "automation_type": "documentation_update_draft",
            "agent_name": "Documentation Gate",
            "source_name": "README.md",
            "source_text": "audit_id: demo-789\n# Demo\n" + ("x" * 5001),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["governance_warnings"]
    assert "warn_large_files" in payload["output_json"]["governance"]["rule_triggered"]
