# ADR 0012: Evidence Grounding Before Generation

## Status

Accepted

## Context

Clinical answers should only be generated when retrieved evidence is present and policy checks pass. Unconstrained generation increases unsafe hallucination risk.

## Decision

Require evidence and policy validation before allowing answer generation, and return refusal/clarification paths otherwise.

## Consequences

- The model is treated as a conditional component, not a default source of truth.
- Weak retrieval can be handled with explicit safe outcomes.
- Citations and evidence metadata become first-class response artifacts.

Trade-off:
- Legitimate but weakly represented questions may be refused until corpus quality improves.
