# Retrieval Failure Triage

Use this runbook when `/ask` returns unexpected insufficient-evidence responses,
retrieval hit rate drops, or vector-store health checks fail.

## First Checks

1. Check `/health/ready` for dependency readiness.
2. Check `/metrics` for retrieval hit-rate changes.
3. Confirm `SYNC_MODE` is set correctly for the environment.
4. Check whether PGVector is reachable in `PG_ONLY` mode.
5. Check whether ChromaDB fallback is available in `DUAL_WRITE` mode.

## Evidence Checks

1. Verify the document was ingested.
2. Verify chunks contain source metadata.
3. Verify chunks contain `risk_level`.
4. Run vector reconciliation if dual-write drift is suspected.
5. Run the golden retrieval evaluation before changing thresholds.

## Escalation Notes

Do not lower refusal thresholds as a first response. Treat threshold changes as
governance changes that require review.
