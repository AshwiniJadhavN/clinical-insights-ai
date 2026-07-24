# Engineering Readiness

Scope, non-claims, and public-sharing boundaries are defined in `DISCLAIMER.md`. This repository is not a certified healthcare production system.

## Implemented Checks

- Dockerized FastAPI service
- Docker Compose with PostgreSQL
- PGVector retrieval path
- ChromaDB local demo path
- Risk-based refusal thresholds
- Canary adversarial tests
- JSONL audit records with hash chaining
- Audit-chain verification CLI
- Retrieval evaluation gate
- Vector-store reconciliation CLI
- Prometheus metrics
- Split Kubernetes liveness/readiness probes

See also:

- `FAILURE_MODES.md`
- `docs/prr/confidence_signal.md`
- `docs/prr/traceability_review.md`
- `docs/prr/embedding_versioning.md`
- `docs/prr/healthcare_governance.md`
- `docs/prr/architecture_accuracy_review.md`

## Not Ready For Clinical Production Use Without More Work

- Clinical validation by qualified domain experts
- HIPAA security risk assessment
- FDA regulatory review, if applicable
- PHI data handling review
- Centralized immutable audit storage
- Role-based access control
- Formal incident response process
- Disaster recovery testing
- Load testing and capacity planning
- Real retrieval quality monitoring on production traffic
- Unified replayable query trace records
- Explicit embedding/chunking version compatibility enforcement

## Positioning

This project demonstrates the engineering wrapper around AI systems: safety gates,
auditability, CI/CD, deployment controls, refusal behavior, and operational checks.
It should not be positioned as a real clinical decision system.