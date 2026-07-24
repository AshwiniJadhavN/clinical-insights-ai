import json
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from backend.audit.search import require_audit_search_access, search_audit_trail
from backend.config import Settings


def test_search_audit_trail_filters_jsonl_records(tmp_path) -> None:
    trail = tmp_path / "trail"
    trail.mkdir()
    entry = {
        "timestamp": "2026-07-06T10:00:00+00:00",
        "audit_id": "audit-1",
        "input_hash": "hash-1",
        "approval_status": "approved",
    }
    (trail / "audit.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")

    results = search_audit_trail(
        trail,
        audit_id="audit-1",
        input_hash="hash-1",
        start_time=datetime(2026, 7, 6, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 7, 6, 11, 0, tzinfo=timezone.utc),
        approval_status="approved",
    )

    assert results == [entry]


def test_search_audit_trail_rejects_invalid_approval_status(tmp_path) -> None:
    with pytest.raises(ValueError):
        search_audit_trail(tmp_path, approval_status="unknown")


def test_audit_search_access_accepts_valid_api_key() -> None:
    settings = Settings(audit_search_api_key="secret")
    request = _Request("203.0.113.10")

    require_audit_search_access(request, settings, x_audit_api_key="secret")


def test_audit_search_access_blocks_external_without_key() -> None:
    settings = Settings(audit_search_api_key="")
    request = _Request("8.8.8.8")

    with pytest.raises(HTTPException):
        require_audit_search_access(request, settings)


class _Client:
    def __init__(self, host: str) -> None:
        self.host = host


class _Request:
    def __init__(self, host: str) -> None:
        self.client = _Client(host)
