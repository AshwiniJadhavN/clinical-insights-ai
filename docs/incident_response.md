# Incident Response Runbook

## Retrieval Quality Drop

1. Run `python scripts/run_retrieval_eval.py`.
2. Review failing golden cases.
3. Check recent chunking, embedding model, and threshold changes.
4. Run vector reconciliation if dual-write mode is enabled.
5. Roll back the change if high-risk retrieval fails.

## Vector Store Divergence

1. Run `python -m backend.cli.reconcile_vectors --json`.
2. If PGVector is missing records, run `python -m backend.cli.sync_vectors`.
3. Re-run reconciliation.
4. Keep `SYNC_MODE=PG_ONLY` for production once PGVector is verified.

## Audit Integrity Failure

1. Run `python -m backend.cli.verify_audit_chain data/agentic_audit.jsonl`.
2. Preserve the suspect audit file.
3. Compare with centralized or object-storage copies if available.
4. Treat any hash-chain break as possible tampering.

## Secret Leak Detected

1. Revoke the exposed secret.
2. Rotate dependent credentials.
3. Review Gitleaks output.
4. Remove the secret from future commits.

## Readiness Failure

1. Check `/health/live` to confirm the Python process is running.
2. Check `/health/ready` for dependency readiness.
3. Inspect PostgreSQL/PGVector connectivity.
4. Keep the pod out of service until readiness returns `200`.
