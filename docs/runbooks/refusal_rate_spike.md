# Refusal Rate Spike

Use this runbook when refusal responses increase unexpectedly.

## First Checks

1. Compare current refusal rate against the last successful deployment.
2. Review recent changes to `backend/governance/rules.yml`.
3. Check whether a model, embedding, or retrieval config changed.
4. Review recent canary test results.
5. Search audit records for common refusal reasons.

## Common Causes

- Governance rules became too broad.
- Risk thresholds changed for `HIGH` or `MEDIUM` content.
- Retrieval quality degraded after embedding or chunking changes.
- Source documents were removed or not ingested.
- Prompt-injection guardrails are correctly blocking a new unsafe pattern.

## Safe Response

Keep the system fail-closed while investigating. Prefer improving ingestion,
retrieval quality, or governance specificity before relaxing refusal logic.
