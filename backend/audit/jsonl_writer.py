"""
Append-only JSONL audit writer.

This module centralizes audit persistence so advisory/governance actions keep a
compatible schema and tests can verify the write behavior directly.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any


class JsonlAuditWriter:
    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, entry: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        previous_hash = _last_record_hash(self._path)
        chained_entry = dict(entry)
        chained_entry["previous_hash"] = previous_hash
        chained_entry["record_hash"] = _record_hash(chained_entry)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(chained_entry, default=str) + "\n")


def verify_hash_chain(path: Path) -> tuple[bool, str]:
    previous_hash = "GENESIS"
    if not path.exists():
        return True, "Audit file does not exist."

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                return False, f"Line {line_number} is not valid JSON."
            expected_previous = entry.get("previous_hash")
            if expected_previous != previous_hash:
                return False, f"Line {line_number} previous_hash mismatch."
            expected_record_hash = entry.get("record_hash")
            if expected_record_hash != _record_hash(entry):
                return False, f"Line {line_number} record_hash mismatch."
            previous_hash = str(expected_record_hash)
    return True, "Audit hash chain verified."


def _last_record_hash(path: Path) -> str:
    if not path.exists():
        return "GENESIS"
    last_hash = "GENESIS"
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            last_hash = str(entry.get("record_hash", last_hash))
    return last_hash


def _record_hash(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "record_hash"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
