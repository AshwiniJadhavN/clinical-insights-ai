# ADR 0013: Explicit Safety Policy Layer

## Status

Accepted

## Context

Safety behavior must be inspectable and testable. Relying only on prompt instructions would make refusal behavior implicit and harder to verify.

## Decision

Implement a dedicated safety policy layer with explicit decision outcomes (`answer`, `clarify`, `refuse`, `insufficient_evidence`) based on input checks, evidence checks, and output/citation validation.

## Consequences

- Safety outcomes are deterministic at policy level and easier to test.
- Input, evidence, and output checks remain separable controls.
- Governance and audit can consume explicit decision metadata.

Trade-off:
- Policy tuning requires disciplined regression testing to avoid unintended refusal/allow changes.
