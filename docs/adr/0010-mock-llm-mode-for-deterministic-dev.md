# ADR 0010: Mock LLM Mode for Deterministic Development Paths

## Status

Accepted

## Context

Development and demonstration workflows need to run without external model keys, provider latency, or variable model outputs.

## Decision

Provide `MOCK_LLM` and fake generator pathways for deterministic local/dev behavior.

## Consequences

- Local onboarding and demos are reliable without provider setup.
- Core safety/retrieval flow can be exercised offline.
- CI and smoke tests can validate transport and orchestration with fewer external dependencies.

Trade-off:
- Mock mode can conceal provider-specific failures and performance issues; production-like validation still requires non-mock test runs.
