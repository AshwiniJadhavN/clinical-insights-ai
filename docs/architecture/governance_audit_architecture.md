# Governance and Audit Architecture

## Purpose

This view explains how policy enforcement and traceability are implemented across query, advisory, and human-review workflows.

## Diagram

```mermaid
flowchart TD
	AdvisoryRequest[Advisory Draft Request] --> GovernanceRuleEngine[GovernanceRuleEngine]
	GovernanceRuleEngine -->|allowed| AdvisoryRoute[backend/api/agentic.py]
	GovernanceRuleEngine -->|blocked| GovernanceAudit[data/agentic_audit.jsonl]

	QueryRequest[Clinical Query Request] --> QueryService[backend/services/query_service.py]
	QueryService --> QueryAudit[backend/services/audit_service.py]
	QueryAudit --> SQLAudit[(SQL audit records)]

	HumanReview[Reviewer Decision] --> ReviewAPI[backend/api/review.py]
	ReviewAPI --> ReviewTrail[reviewer_decisions.jsonl]

	AuditSearch[/audit/search] --> AuditRead[backend/audit/search.py]
	AuditRead --> ReviewTrail
	AuditRead --> GovernanceAudit
	AuditRead --> SQLAudit
```

## Implementation Mapping

- Governance rules endpoint: `backend/api/governance.py` exposes loaded rule state for observability.
- Advisory governance gate: `backend/api/agentic.py` evaluates `GovernanceRuleEngine` before any draft generation. The primary route is `/advisory/draft`; `/agentic/draft` remains a hidden compatibility alias.
- Governance block logging: blocked advisory requests are written to `data/agentic_audit.jsonl` through `JsonlAuditWriter`.
- Query audit logging: `backend/services/audit_service.py` records query metadata in SQL without storing raw question or answer text.
- Audit read endpoint: `backend/api/audit.py` returns recent entries and degrades to an empty list if the database is unavailable.
- Human review decisions: `backend/api/review.py` and `backend/services/review_service.py` append reviewer actions to JSONL.
- Audit search: `backend/main.py` exposes `/audit/search` with access checks and bounded result limits.

## Control Boundaries

- Governance controls automation requests before draft output is returned.
- Safety controls answer behavior before the response reaches the client.
- Audit controls preserve traceability for query outcomes, governance blocks, and review decisions.

## Engineering Rationale

The architecture separates policy enforcement from logging and retrieval so each control can evolve independently. This improves explainability during compliance-oriented reviews and avoids coupling business logic with persistence details.

## Verification Strategy

- API tests verify governance rules can block draft automation.
- Service tests verify audit writes never crash request handling.
- Review tests verify decisions are append-only and traceable.
