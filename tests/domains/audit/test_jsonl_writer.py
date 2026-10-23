import json
from concurrent.futures import ThreadPoolExecutor

from backend.audit.jsonl_writer import JsonlAuditWriter, verify_hash_chain


def test_jsonl_writer_appends_json_lines_and_creates_parent(tmp_path) -> None:
    audit_path = tmp_path / "audit" / "events.jsonl"
    writer = JsonlAuditWriter(audit_path)

    writer.append({"timestamp": "2026-07-06T00:00:00Z", "audit_id": "a-1", "action": "test"})
    writer.append({"timestamp": "2026-07-06T00:00:01Z", "audit_id": "a-2", "action": "test"})

    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert [row["audit_id"] for row in rows] == ["a-1", "a-2"]
    assert rows[0]["previous_hash"] == "GENESIS"
    assert rows[1]["previous_hash"] == rows[0]["record_hash"]
    assert verify_hash_chain(audit_path) == (True, "Audit hash chain verified.")


def test_jsonl_writer_detects_tampering(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    writer = JsonlAuditWriter(audit_path)
    writer.append({"timestamp": "2026-07-06T00:00:00Z", "audit_id": "a-1", "action": "test"})
    row = json.loads(audit_path.read_text(encoding="utf-8"))
    row["action"] = "tampered"
    audit_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    ok, message = verify_hash_chain(audit_path)

    assert ok is False
    assert "record_hash mismatch" in message


def test_hash_chain_verifier_handles_missing_file(tmp_path) -> None:
    assert verify_hash_chain(tmp_path / "missing.jsonl") == (
        True,
        "Audit file does not exist.",
    )


def test_hash_chain_verifier_skips_blank_lines_and_rejects_invalid_json(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    audit_path.write_text("\nnot-json\n", encoding="utf-8")

    ok, message = verify_hash_chain(audit_path)

    assert ok is False
    assert "not valid JSON" in message


def test_hash_chain_verifier_detects_previous_hash_mismatch(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    writer = JsonlAuditWriter(audit_path)
    writer.append({"timestamp": "2026-07-06T00:00:00Z", "audit_id": "a-1", "action": "test"})
    row = json.loads(audit_path.read_text(encoding="utf-8"))
    row["previous_hash"] = "wrong"
    audit_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    ok, message = verify_hash_chain(audit_path)

    assert ok is False
    assert "previous_hash mismatch" in message


def test_jsonl_writer_ignores_invalid_existing_lines_when_appending(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    audit_path.write_text("not-json\n\n", encoding="utf-8")
    JsonlAuditWriter(audit_path).append(
        {"timestamp": "2026-07-06T00:00:00Z", "audit_id": "a-1", "action": "test"}
    )

    row = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])

    assert row["previous_hash"] == "GENESIS"


def test_jsonl_writer_preserves_hash_chain_during_concurrent_appends(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"

    def append(index: int) -> None:
        JsonlAuditWriter(audit_path).append(
            {"timestamp": f"2026-07-06T00:00:{index:02d}Z", "audit_id": f"a-{index}"}
        )

    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(append, range(100)))

    assert len(audit_path.read_text(encoding="utf-8").splitlines()) == 100
    assert verify_hash_chain(audit_path) == (True, "Audit hash chain verified.")
