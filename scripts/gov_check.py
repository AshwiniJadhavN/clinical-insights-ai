#!/usr/bin/env python3
"""
Run governance rules against a JSON payload.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.governance.rule_engine import GovernanceRuleEngine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate governance rules against a JSON payload.")
    parser.add_argument("payload", type=Path, help="Path to JSON payload file.")
    parser.add_argument(
        "--rules",
        type=Path,
        default=ROOT / "backend" / "governance" / "rules.yml",
        help="Path to governance rules.yml.",
    )
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    result = GovernanceRuleEngine(args.rules).evaluate(payload)

    if result.blocked:
        print(f"FAIL: blocked by {', '.join(result.rule_triggered)}")
        for warning in result.warnings:
            print(f"- {warning}")
        return 1

    if result.warnings:
        print(f"WARN: {', '.join(result.rule_triggered)}")
        for warning in result.warnings:
            print(f"- {warning}")
        return 0

    print("PASS: governance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
