# ADR 0005: Tamper-Evident Audit Log

## Status

Accepted

## Context

Plain JSONL audit files are easy to inspect but do not show whether records were
changed after writing.

## Decision

Add hash chaining to audit records:

- `previous_hash`
- `record_hash`

Provide a CLI verifier that exits nonzero when the chain is broken.

## Consequences

The audit trail becomes tamper-evident for demonstration and review purposes. This is
not a substitute for immutable, centralized production audit storage.
