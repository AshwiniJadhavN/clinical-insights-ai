# ADR 0009: GitHub Actions as CI Quality Gate

## Status

Accepted

## Context

The project needs deterministic, reviewable checks for code quality, tests, and packaging readiness on every change.

## Decision

Use GitHub Actions as the default CI pipeline for lint, tests, security scans, and build validation.

## Consequences

- Every pull request is evaluated by the same automated checks.
- CI definitions are versioned with the codebase.
- Release-readiness discussion can reference concrete, reproducible gate outputs.

Trade-off:
- Pipeline reliability depends on external CI availability and workflow maintenance.
