# Observability Playbook (Lite)

This note captures practical observability signals for local and demo environments.

## Structured Logging

- Include correlation IDs (`X-Request-ID`) on inbound and outbound HTTP paths.
- Keep logs machine-parseable and safe (no secrets, no PHI payload dumps).
- Record key decision metadata: safety decision, refusal reason, evidence status.

## Key Metrics and Alerts

Primary metrics exposed in [backend/main.py](../../backend/main.py):

- `clinical_insights_app_info`
- `clinical_insights_indexed_chunks`
- `clinical_insights_http_requests_total`

Recommended alert ideas:

1. Readiness failures: `/health/ready` non-200 for 5 minutes.
2. Refusal spike: sudden increase in refusal/insufficient-evidence outcomes.
3. Retrieval degradation: retrieval eval misses increase in CI trend.
4. Error burst: sustained 5xx increase on `/ask` or `/query`.

## Incident Playbook-Lite

1. Confirm service liveness and readiness (`/health/live`, `/health/ready`).
2. Pull recent structured logs by correlation ID.
3. Check latest CI artifacts for retrieval/refusal regressions.
4. If risk is high, roll back to last known good revision.
5. Document impact, mitigation, and follow-up tests.

Detailed runbook: [docs/incident_response.md](../incident_response.md)