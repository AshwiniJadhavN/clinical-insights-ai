# ADR 0006: FastAPI as Service Boundary

## Status

Accepted

## Context

The project needs a typed HTTP boundary that supports:

- schema-first request/response validation
- dependency injection for swappable runtime components
- OpenAPI documentation for demonstration and review
- simple local execution with minimal infrastructure

## Decision

Use FastAPI as the backend service framework.

FastAPI routers remain thin transport boundaries, while orchestration stays in services and domain modules.

## Consequences

- Strong runtime contracts through Pydantic models and generated OpenAPI docs.
- Testability is improved through dependency injection and replaceable fakes.
- Team can keep architecture layered without introducing custom transport abstractions.

Trade-off:
- Async/sync boundaries and dependency wiring must be maintained carefully to avoid hidden complexity.
