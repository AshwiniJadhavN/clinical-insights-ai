# ADR 0011: Audit Logging for Reviewability

## Status

Accepted

## Context

The platform needs post-hoc visibility into what happened during query and advisory workflows, while minimizing sensitive content retention.

## Decision

Maintain explicit audit logging:

- SQL query audit metadata for clinical Q&A events
- JSONL append-only records (with hash chaining) for advisory/governance/review flows

## Consequences

- Investigations and demos can trace key decisions and outcomes.
- Sensitive raw question/answer text is not stored in SQL query audit entries.
- Advisory trail tampering can be detected with hash-chain verification.

Trade-off:
- Audit data currently spans multiple stores and is not yet a unified immutable ledger.
