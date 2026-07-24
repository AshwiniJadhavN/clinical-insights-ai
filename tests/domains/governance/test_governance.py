import json
import pytest

from fastapi.testclient import TestClient

from backend.governance.rule_engine import GovernanceRuleEngine
from backend.main import app


def test_governance_engine_blocks_sensitive_source_name() -> None:
    result = GovernanceRuleEngine().evaluate(
        {
            "source_name": "secrets/prod.key",
            "source_text": "audit_id: test\n+ change",
        }
    )

    assert result.blocked is True
    assert "block_sensitive_files" in result.rule_triggered


def test_governance_engine_warns_on_large_source_text() -> None:
    result = GovernanceRuleEngine().evaluate(
        {
            "source_name": "README.md",
            "source_text": "audit_id: test\n" + ("x" * 5001),
        }
    )

    assert result.blocked is False
    assert result.warnings
    assert "warn_large_files" in result.rule_triggered


def test_governance_rules_endpoint_returns_loaded_rules() -> None:
    response = TestClient(app).get("/governance/rules")

    assert response.status_code == 200
    rule_ids = [rule["id"] for rule in response.json()["rules"]]
    assert "block_sensitive_files" in rule_ids
    assert "require_traceability" in rule_ids


def test_governance_cli_passes_for_traceable_payload(tmp_path) -> None:
    payload = tmp_path / "payload.json"
    payload.write_text(
        json.dumps(
            {
                "source_name": "backend/main.py",
                "source_text": "audit_id: cli-test\n+ app.include_router(router)",
            }
        ),
        encoding="utf-8",
    )

    result = GovernanceRuleEngine().evaluate(json.loads(payload.read_text(encoding="utf-8")))

    assert result.passed is True


def test_governance_engine_rejects_invalid_rules_file(tmp_path) -> None:
    rules = tmp_path / "rules.yml"
    rules.write_text("not_rules: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="top-level 'rules'"):
        GovernanceRuleEngine(rules).load_rules()


def test_governance_engine_ignores_unknown_or_malformed_rules(tmp_path) -> None:
    rules = tmp_path / "rules.yml"
    rules.write_text(
        """
rules:
  - malformed
  - id: unknown_operator
    mode: blocking
    operator: does_not_exist
""",
        encoding="utf-8",
    )

    result = GovernanceRuleEngine(rules).evaluate({"source_name": "README.md"})

    assert result.passed is True
    assert result.rule_triggered == []
