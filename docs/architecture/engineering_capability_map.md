# Engineering Capability Map

## Purpose

This view summarizes what the repository demonstrates across AI application engineering, backend design, and DevOps checks.

## Diagram

```mermaid
flowchart TD
	A[Runtime Service Boundary] --> B[AI Application Engineering]
	A --> C[Software Architecture]
	A --> D[Quality and DevOps]

	B --> B1[Retrieval before generation]
	B --> B2[Refusal on weak evidence]
	B --> B3[Safety decision engine]
	B --> B4[AI-assisted integration testing]

	C --> C1[FastAPI route and schema boundaries]
	C --> C2[Service orchestration layer]
	C --> C3[Typed configuration and validation]
	C --> C4[Audit and governance controls]

	D --> D1[CI quality gates]
	D --> D2[Coverage and canary checks]
	D --> D3[Health, metrics, and logging]
	D --> D4[Containerized local runtime]
```

## Evidence in Repository Structure

- Systems engineering evidence: `backend/main.py`, `backend/core/bootstrap.py`, `backend/schemas/health.py`.
- AI engineering evidence: `backend/retrieval/`, `backend/services/query_service.py`, `backend/refusal/logic.py`, `backend/safety/decision_engine.py`.
- Software architecture evidence: `backend/api/`, `backend/services/`, `backend/schemas/`, `tests/`.
- DevOps evidence: `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, `scripts/test.sh`, `scripts/smoke_test.sh`.

## Engineering Narrative

- The application does not treat model output as inherently trusted.
- Evidence quality determines whether generation is allowed.
- Governance and audit controls provide explicit reviewability.
- CI and runtime checks provide operational confidence.

## Why This Matters

This capability map helps reviewers quickly see that the repository demonstrates maintainable AI application engineering, not just prompt orchestration or UI integration.
