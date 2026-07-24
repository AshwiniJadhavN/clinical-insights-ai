"""Search JSONL audit trails with safe filters and bounded results."""

from __future__ import annotations

import ipaddress
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Header, HTTPException, Request

from backend.config import Settings

MAX_AUDIT_SEARCH_RESULTS = 1000
ALLOWED_APPROVAL_STATUSES = {"pending", "approved", "refused", "draft_needs_human_review"}


def require_audit_search_access(
    request: Request,
    settings: Settings,
    x_audit_api_key: str | None = Header(default=None, alias="X-Audit-API-Key"),
) -> None:
    if settings.audit_search_api_key:
        if x_audit_api_key != settings.audit_search_api_key:
            raise HTTPException(status_code=403, detail="Audit search access denied.")
        return

    host = request.client.host if request.client else ""
    if not _is_internal_address(host):
        raise HTTPException(status_code=403, detail="Audit search access denied.")


def search_audit_trail(
    trail_directory: Path,
    audit_id: str | None = None,
    input_hash: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    approval_status: str | None = None,
    limit: int = MAX_AUDIT_SEARCH_RESULTS,
) -> list[dict[str, Any]]:
    if approval_status and approval_status not in ALLOWED_APPROVAL_STATUSES:
        raise ValueError("approval_status must be one of pending, approved, refused.")

    bounded_limit = min(max(limit, 1), MAX_AUDIT_SEARCH_RESULTS)
    results: list[dict[str, Any]] = []
    for path in _audit_files(trail_directory):
        for entry in _read_jsonl(path):
            if _matches(entry, audit_id, input_hash, start_time, end_time, approval_status):
                results.append(entry)
                if len(results) >= bounded_limit:
                    return results
    return results


def _audit_files(trail_directory: Path) -> list[Path]:
    files = sorted(trail_directory.glob("*.jsonl")) if trail_directory.exists() else []
    legacy_file = Path("data/agentic_audit.jsonl")
    if legacy_file.exists():
        files.append(legacy_file)
    return files


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _matches(
    entry: dict[str, Any],
    audit_id: str | None,
    input_hash: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    approval_status: str | None,
) -> bool:
    if audit_id and entry.get("audit_id") != audit_id:
        return False
    if input_hash and entry.get("input_hash") != input_hash:
        return False
    if approval_status and _normalized_status(str(entry.get("approval_status", ""))) != approval_status:
        return False
    timestamp = _parse_time(str(entry.get("timestamp", "")))
    if start_time and (timestamp is None or timestamp < start_time):
        return False
    if end_time and (timestamp is None or timestamp > end_time):
        return False
    return True


def _normalized_status(value: str) -> str:
    if value in {"approved", "refused", "pending"}:
        return value
    if "approved" in value:
        return "approved"
    if "refused" in value or "blocked" in value:
        return "refused"
    return value or "pending"


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_internal_address(host: str) -> bool:
    if host in {"localhost", "testclient"}:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback
