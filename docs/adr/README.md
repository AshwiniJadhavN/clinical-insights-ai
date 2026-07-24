# ADR Index

This index highlights key architecture decisions with alternatives and rationale.

## Core Decisions

| Decision | ADR | Alternatives considered | Rationale |
|---|---|---|---|
| Risk-based refusal thresholds | [0004-risk-based-refusal-thresholds.md](0004-risk-based-refusal-thresholds.md) | Always answer, fixed binary blocklist | Threshold-driven refusal balances answer utility and safety under weak evidence. |
| Tamper-evident audit log | [0005-tamper-evident-audit-log.md](0005-tamper-evident-audit-log.md) | Plain append-only logs without chaining | Hash-chained records improve reviewability and tamper detection. |
| FastAPI service boundary | [0006-fastapi-as-service-boundary.md](0006-fastapi-as-service-boundary.md) | Direct scripts only, monolithic worker | Explicit API boundaries improve testability, observability, and deployment controls. |
| Quality gates in CI | [0009-github-actions-quality-gates.md](0009-github-actions-quality-gates.md) | Manual validation only, ad-hoc checks | Automated gates make regressions and safety drift visible before merge. |

## Additional ADRs

- [0001-layered-domain-architecture.md](0001-layered-domain-architecture.md)
- [0002-configuration-as-code.md](0002-configuration-as-code.md)
- [0003-dual-vector-store-sync.md](0003-dual-vector-store-sync.md)
- [0007-retrieval-augmented-generation.md](0007-retrieval-augmented-generation.md)
- [0008-docker-compose-for-local-orchestration.md](0008-docker-compose-for-local-orchestration.md)
- [0010-mock-llm-mode-for-deterministic-dev.md](0010-mock-llm-mode-for-deterministic-dev.md)
- [0011-audit-logging-for-reviewability.md](0011-audit-logging-for-reviewability.md)
- [0012-evidence-grounding-before-generation.md](0012-evidence-grounding-before-generation.md)
- [0013-safety-policy-layer.md](0013-safety-policy-layer.md)
- [ADR-004-refusal-on-weak-evidence.md](ADR-004-refusal-on-weak-evidence.md)