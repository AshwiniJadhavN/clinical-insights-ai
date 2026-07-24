# ADR 0001: Layered Domain-Oriented Architecture

## Status

Accepted

## Context

The project started as a FastAPI clinical RAG demo and grew into a platform
showing governance, safety, auditability, observability, and deployment controls.
A purely technical folder structure would make the business boundaries harder
to explain.

## Decision

Use a layered, domain-oriented structure:

- `backend/api/` for HTTP boundaries
- `backend/services/` for workflow orchestration
- `backend/core/` for domain boundary documentation and bootstrap wiring
- `backend/governance/`, `backend/audit/`, `backend/retrieval/`, `backend/refusal/`
  for domain-specific policy and logic
- `config/` for YAML configuration

## Consequences

The code remains compatible with the existing FastAPI layout while making the
domain boundaries clearer for reviewers and AI assistants.
