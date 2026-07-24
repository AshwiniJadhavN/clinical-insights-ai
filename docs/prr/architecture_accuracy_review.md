# Architecture Accuracy Review

Date: 2026-07-08

Objective: ensure architecture-facing documentation does not overstate implementation.

## Reviewed Sources

- `README.md`
- `docs/architecture.md`
- `docs/architecture/README.md`
- `docs/architecture/ai_architecture.md`
- `docs/architecture/sequence_diagrams.md`
- `docs/deployment.md`

## Corrections Applied

1. Replaced "production-grade" framing with demonstration-scoped wording.
2. Clarified that confidence in responses is a retrieval heuristic, not a probability.
3. Removed wording that implied universal guarantees for local mock-mode startup.
4. Clarified that query audit and JSONL advisory audit are separate paths rather than a single unified ledger.
5. Updated response/diagram labels to avoid probabilistic interpretation of confidence.

## Statements Intentionally Kept

The following claims remain because they are directly supported in code:

- Input screening before query processing.
- Evidence-gated generation with refusal/clarification paths.
- Audit metadata capture for query and advisory/review workflows.
- Docker/Compose-based local deployment paths.
- Health/readiness/metrics endpoints.

## Remaining Accuracy Risks

- Broader narrative docs outside the implementation-first architecture package may still contain historical phrasing.
- Some diagrams describe optional or future deployment targets and should continue to be marked as reference architecture when applicable.

## Maintenance Guidance

When architecture docs are edited, verify each claim against:

- Runtime wiring in `backend/core/bootstrap.py`
- Query orchestration in `backend/services/query_service.py`
- Audit persistence paths in `backend/services/audit_service.py` and `backend/audit/jsonl_writer.py`
- API contracts in `backend/schemas/`
