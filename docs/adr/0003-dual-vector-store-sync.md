# ADR 0003: Dual Vector Store Sync

## Status

Accepted

## Context

ChromaDB is useful for local demos, while PGVector is a better database-backed
retrieval option when PostgreSQL is already part of the runtime.

## Decision

Support two sync modes:

- `DUAL_WRITE`: write to ChromaDB and PGVector, read PGVector first with Chroma fallback
- `PG_ONLY`: disable ChromaDB and fail fast if PGVector is unavailable

Provide reconciliation and backfill CLIs to detect and repair drift.

## Consequences

The demo remains easy to run while showing a credible production migration path.
The tradeoff is extra operational complexity, addressed through reconciliation.
