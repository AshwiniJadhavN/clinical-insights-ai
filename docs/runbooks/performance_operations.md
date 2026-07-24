# Performance Operations Runbook

This runbook defines how to monitor, debug, and scale Clinical Insights AI under
load. The project is a demonstration repository only and is not a medical device.

## Key Runtime Signals

- `/health/live`: confirms the Python process is alive.
- `/health/ready`: confirms dependencies are ready for traffic.
- `/metrics`: exposes Prometheus metrics for request count, indexed chunks,
  retrieval hit rate, and advisory refusal counters.
- Application logs: include request IDs and correlation IDs for request-level
  tracing.
- Audit records: preserve safety and advisory decisions for post-event review.

## Baseline Checks

Run these checks before a load test or demo:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/metrics
```

Expected result:

- Liveness returns `{"status":"live"}`.
- Readiness returns `{"status":"ready"}` after dependencies initialize.
- Metrics endpoint returns Prometheus text output.

## Common Bottlenecks

| Symptom | Likely Cause | First Check |
|---|---|---|
| Slow first request | embedding model cold start | container logs and startup time |
| High refusal rate | weak retrieval or missing documents | retrieval hit-rate metric and audit entries |
| Slow `/ask` responses | vector search or LLM timeout | request logs, retrieval count, model timeout |
| Readiness flapping | database/vector store latency | `/health/ready`, Compose logs, DB health |
| Large memory use | embedding model and vector index growth | container memory and indexed chunk count |

## Debugging Workflow

1. Confirm process health with `/health/live`.
2. Confirm dependency readiness with `/health/ready`.
3. Check `/metrics` for request volume, retrieval hit rate, and refusal counters.
4. Search logs by `X-Request-ID` or `correlation_id`.
5. Review audit records for safety decisions and refusal reasons.
6. Reproduce locally with `MOCK_LLM=true` to separate platform issues from model/provider issues.
7. Re-run `make ci-local` before applying a fix.

## Scaling Guidance

- Scale API replicas horizontally when CPU or request latency rises.
- Keep `/health/live` lightweight so Kubernetes does not restart healthy pods
  during dependency cold starts.
- Use `/health/ready` to hold traffic until database/vector dependencies are
  ready.
- Prefer `PG_ONLY` sync mode for production-style deployments where PostgreSQL
  with PGVector is the source of truth.
- Keep `DUAL_WRITE` for local demos where Chroma fallback improves developer
  ergonomics.

## Load-Test Checklist

- Use synthetic documents only.
- Seed a small, known document set before testing.
- Track p50, p95, and p99 latency for `/ask`.
- Track refusal rate and retrieval hit rate together.
- Verify no raw clinical text appears in logs.
- Capture Docker/container CPU and memory during the run.

## Escalation Criteria

Escalate for engineering review when:

- p95 `/ask` latency increases by more than 2x from baseline.
- readiness fails for more than 2 consecutive minutes.
- retrieval hit rate drops sharply after a model/chunking change.
- advisory refusal counters spike unexpectedly.
- audit writes fail or audit chain verification fails.
