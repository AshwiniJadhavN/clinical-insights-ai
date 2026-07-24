# 001 - Domain-Driven Structure (Strangler Pattern)

**Status:** Accepted
**Date:** 2026-07-07
**Decision:** Adopt a `backend/domains/` structure incrementally via a strangler pattern, rather than a wholesale `backend/` -> `src/` rename.

**Context:**
The repo began as a functional prototype with `backend/rag/`, `backend/refusal/`, etc. While logically separated, these folders are parallel rather than explicitly domain-bounded. A full restructure would invalidate Docker layer caching, break GitHub Actions path filters, and create costly merge conflicts across open PRs.

**Consequences:**
- We will create `backend/domains/` as an empty package initially.
- Each domain (refusal, audit, governance, retrieval) will be migrated one at a time using compatibility shims.
- We will not rename `backend/` to `src/` in this cycle.
- All new domain logic will be placed directly in `backend/domains/`.

**Target Layout:**

```text
.
|-- backend/
|   |-- api/
|   |-- core/
|   |-- domains/          <-- New home for business capabilities
|   |   |-- retrieval/
|   |   |-- refusal/
|   |   |-- governance/
|   |   `-- audit/
|   |-- schemas/
|   |-- models/
|   `-- services/         (will be phased out as logic migrates to domains)
|-- evaluation/           (CI-time retrieval eval and golden datasets)
|-- config/
`-- tests/
```
