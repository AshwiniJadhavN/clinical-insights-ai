#!/usr/bin/env python3
"""Enforce 100% coverage on safety-critical modules."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CRITICAL_FILES = {
    "backend/governance/rule_engine.py",
    "backend/governance/rules_engine.py",
    "backend/refusal/logic.py",
    "backend/audit/jsonl_writer.py",
    "governance/rule_engine.py",
    "governance/rules_engine.py",
    "refusal/logic.py",
    "audit/jsonl_writer.py",
}


def _critical(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    return normalized in CRITICAL_FILES or "guardrail" in normalized.lower()


def main() -> int:
    xml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("coverage.xml")
    tree = ET.parse(xml_path)
    failures: list[str] = []
    seen: set[str] = set()

    for class_node in tree.findall(".//class"):
        filename = str(class_node.attrib.get("filename", "")).replace("\\", "/")
        if not _critical(filename):
            continue
        seen.add(filename)
        line_rate = float(class_node.attrib.get("line-rate", "0")) * 100
        if line_rate < 100:
            failures.append(f"{filename}: {line_rate:.2f}%")

    required_groups = {
        "governance/rule_engine.py": {"backend/governance/rule_engine.py", "governance/rule_engine.py"},
        "refusal/logic.py": {"backend/refusal/logic.py", "refusal/logic.py"},
        "audit/jsonl_writer.py": {"backend/audit/jsonl_writer.py", "audit/jsonl_writer.py"},
    }
    missing = [
        display
        for display, accepted_names in required_groups.items()
        if seen.isdisjoint(accepted_names)
    ]
    if missing:
        failures.extend(f"{filename}: missing from coverage report" for filename in missing)

    if failures:
        print("FAIL critical coverage gate:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("PASS critical coverage gate: safety-critical files are at 100%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
