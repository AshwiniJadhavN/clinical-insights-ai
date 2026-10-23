"""
Append-only JSONL audit writer.

This module centralizes audit persistence so advisory/governance actions keep a
compatible schema and tests can verify the write behavior directly.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import threading
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows uses the in-process lock below.
    fcntl = None  # type: ignore[assignment]


_PATH_LOCKS: dict[Path, threading.Lock] = {}
_PATH_LOCKS_GUARD = threading.Lock()


class JsonlAuditWriter:
    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, entry: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lock = _lock_for(self._path)
        with lock, self._path.open("a+", encoding="utf-8") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.seek(0)
                previous_hash = _last_record_hash_from_lines(handle)
                chained_entry = dict(entry)
                chained_entry["previous_hash"] = previous_hash
                chained_entry["record_hash"] = _record_hash(chained_entry)
                handle.seek(0, 2)
                handle.write(json.dumps(chained_entry, default=str) + "\n")
                handle.flush()
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


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
    with path.open("r", encoding="utf-8") as handle:
        return _last_record_hash_from_lines(handle)


def _last_record_hash_from_lines(lines) -> str:
    last_hash = "GENESIS"
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        last_hash = str(entry.get("record_hash", last_hash))
    return last_hash


def _lock_for(path: Path) -> threading.Lock:
    resolved = path.resolve()
    with _PATH_LOCKS_GUARD:
        return _PATH_LOCKS.setdefault(resolved, threading.Lock())


def _record_hash(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "record_hash"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
