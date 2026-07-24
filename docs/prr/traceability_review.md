# Traceability Review (As Implemented)

Date: 2026-07-08

This review documents what is captured today. It does not claim full replayability.

## Query Path (`/ask`, `/query`)

Primary SQL audit source:
- `backend/services/audit_service.py`
- `backend/models/audit_log.py`
- `backend/api/audit.py`

Captured today in SQL audit rows:
- `query_id`
- `question_length` (not raw question)
- `answer_length` (not raw answer)
- `retrieval_count`
- `confidence_score`
- `confidence_level`
- `model_used`
- `safety_decision`
- `refusal_reason`
- `correlation_id` (if present)
- `prompt_version`
- `retrieved_doc_ids` (document ids only)
- `processing_time_ms`
- `review_required`
- `created_at`

Not captured in SQL audit rows:
- raw retrieved chunk text
- full prompt body/template content
- full runtime config snapshot
- citation payloads (doc/chunk offsets/excerpts)
- provider request/response ids
- embedding model/chunking parameters used at query time

## API Response vs Audit Persistence

`QueryResponse` includes citations and `retrieved_chunk` in API response.
These are not persisted in SQL audit rows today.

## Advisory/Governance/Review JSONL Trails

JSONL trail sources:
- `data/agentic_audit.jsonl` (advisory/governance)
- `backend/audit/trail/reviewer_decisions.jsonl` (human review decisions)

Captured in advisory JSONL entries (via `AgenticAuditEntry`):
- timestamp
- audit_id
- action
- input_hash
- agent_name
- model_used
- confidence_score (advisory heuristic)
- evidence_references
- output_json
- approval_status
- hash-chain fields (`previous_hash`, `record_hash`)

Captured in reviewer decision JSONL entries:
- event type
- query_id
- reviewer_id
- decision
- modified answer length
- comments length
- timestamp
- hash-chain fields

## Replayability Statement

Current implementation supports post-hoc review and partial traceability.

It does not currently support deterministic full replay of historical query outcomes, because full prompt text, complete runtime config, and full retrieved evidence payload are not persisted together as an immutable execution record.

## Recommended Non-Breaking Enhancements

1. Add optional query-trace envelope persisted per request (prompt hash, citation payload hash, config snapshot hash).
2. Add explicit audit schema versioning for SQL and JSONL paths.
3. Add correlation-id propagation to all audit events and UI surfaces.
4. Add policy for retention, archival, and redaction governance.
