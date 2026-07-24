# Architecture Notes

This folder documents how the current repository is organized. It is not a target architecture or a compliance package.

The architecture should be read through three questions:

1. How are documents ingested and retrieved?
2. How does the system decide whether answering is allowed?
3. How are the API, tests, runtime, and CI kept maintainable?

## Core Views

- [AI Architecture](ai_architecture.md): document RAG flow, retrieval, confidence heuristic, generation, and refusal path.
- [Software Architecture](software_architecture.md): API routers, services, safety, retrieval, audit, and persistence boundaries.
- [Safety Architecture](safety_architecture.md): input, evidence, citation, output, and policy checks.
- [DevOps Architecture](devops_architecture.md): Docker, Compose, CI, health checks, and smoke checks.
- [Governance and Audit Architecture](governance_audit_architecture.md): audit metadata and review/advisory records.

## Supporting Views

- [System Context](system_context.md)
- [Deployment Architecture](deployment_architecture.md)
- [Runtime Architecture](runtime_architecture.md)
- [Sequence Diagrams](sequence_diagrams.md)
- [Repository Architecture](repository_architecture.md)

## Accuracy Notes

- The frontend is a Vite application; Docker Compose provisions the API and PostgreSQL database.
- `confidence_score` is a similarity-based retrieval heuristic, not a probability of correctness.
- Query audit metadata supports reviewability, but full deterministic replay is not implemented.
- Some advisory/review routes exist as supporting safety/audit examples; the core product workflow is document upload -> retrieval -> answer/refusal.
