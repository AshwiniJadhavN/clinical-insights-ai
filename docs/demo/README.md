# Demo Walk-Through (3 Minutes)

Use this script to present the repository quickly with concrete engineering signals.

## Assets

- Video: [demo.mp4](demo.mp4)
- Preview screenshot: [demo-preview.png](demo-preview.png)

## Timeline

### 0:00-0:30 - Problem and Scope

1. Open [README.md](../../README.md).
2. Call out the scope and non-claims links.
3. State the objective: evidence-grounded clinical document Q&A with refusal controls.

### 0:30-1:20 - Architecture and Safety

1. Show [docs/architecture/software_architecture.md](../architecture/software_architecture.md).
2. Explain the runtime path and where safety decisions are applied.
3. Open [docs/risk_controls.md](../risk_controls.md) for guardrail categories.

### 1:20-2:10 - Testing and CI

1. Show [.github/workflows/ci.yml](../../.github/workflows/ci.yml).
2. Highlight quality gates: lint, tests, type checks, coverage.
3. Show [docs/testing/ai_assisted_integration_report.md](../testing/ai_assisted_integration_report.md).

### 2:10-3:00 - Operations and Readiness

1. Open [docs/engineering_readiness.md](../engineering_readiness.md).
2. Show [docs/runbooks/observability_playbook_lite.md](../runbooks/observability_playbook_lite.md).
3. Close with [docs/engineering_tradeoffs.md](../engineering_tradeoffs.md).

## Suggested Narration

"This demo focuses on engineering controls rather than clinical claims: safety refusals, deterministic evaluation, traceable audits, and CI gates that make failures visible early."