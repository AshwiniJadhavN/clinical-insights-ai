# ADR 0008: Docker Compose for Local Orchestration

## Status

Accepted

## Context

The repository needs a reproducible local runtime that demonstrates multi-service behavior (API + database) without requiring cloud infrastructure.

## Decision

Use Docker Compose for local orchestration of core services.

Compose is used for developer/demo environments, while keeping deployment architecture portable to other orchestrators.

## Consequences

- Local setup is consistent across machines.
- Service dependencies and health checks are explicit.
- Demo and CI narratives can use the same container artifacts.

Trade-off:
- Compose does not provide production-grade orchestration guarantees by itself.
