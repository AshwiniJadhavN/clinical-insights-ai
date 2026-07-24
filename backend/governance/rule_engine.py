"""
YAML-backed governance rule engine for pre-action advisory controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml


DEFAULT_RULES_PATH = Path(__file__).with_name("rules.yml")


@dataclass(frozen=True)
class GovernanceResult:
    passed: bool
    blocked: bool
    warnings: list[str]
    rule_triggered: list[str]

    def model_dump(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "blocked": self.blocked,
            "warnings": self.warnings,
            "rule_triggered": self.rule_triggered,
        }


class GovernanceRuleEngine:
    """Load YAML rules from disk on each evaluation for hot-reload behavior."""

    def __init__(self, rules_path: Path | str = DEFAULT_RULES_PATH) -> None:
        self.rules_path = Path(rules_path)

    def load_rules(self) -> dict[str, Any]:
        with self.rules_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict) or "rules" not in data:
            raise ValueError("Governance rules file must contain a top-level 'rules' key.")
        return data

    def evaluate(self, payload: dict[str, Any]) -> GovernanceResult:
        rules = self.load_rules().get("rules", [])
        warnings: list[str] = []
        triggered: list[str] = []
        blocked = False

        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if not _rule_matches(rule, payload):
                continue
            rule_id = str(rule.get("id", "unknown_rule"))
            message = str(rule.get("message", f"Governance rule triggered: {rule_id}"))
            triggered.append(rule_id)
            if rule.get("mode") == "blocking":
                blocked = True
                warnings.append(message)
            else:
                warnings.append(message)

        return GovernanceResult(
            passed=not blocked,
            blocked=blocked,
            warnings=warnings,
            rule_triggered=triggered,
        )


def _rule_matches(rule: dict[str, Any], payload: dict[str, Any]) -> bool:
    operator = rule.get("operator")
    if operator == "glob_any":
        value = str(payload.get(str(rule.get("field", "")), ""))
        return any(fnmatch(value, pattern) for pattern in rule.get("patterns", []))

    if operator == "max_length":
        value = str(payload.get(str(rule.get("field", "")), ""))
        max_length = int(rule.get("max_length", 0))
        return len(value) > max_length

    if operator == "traceability_required":
        source_name = str(payload.get(str(rule.get("source_name_field", "source_name")), ""))
        audit_text = str(payload.get(str(rule.get("audit_reference_field", "source_text")), ""))
        audit_reference = str(rule.get("audit_reference", "audit_id"))
        return not source_name.strip() or audit_reference not in audit_text

    return False
