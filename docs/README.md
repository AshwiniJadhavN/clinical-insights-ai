# Documentation Index

This directory provides architecture, safety, evaluation, and deployment guidance for **Clinical Insights AI**.

## Start Here

- [Architecture](architecture.md)
- [Engineering Readiness](engineering_readiness.md)
- [Engineering Tradeoffs](engineering_tradeoffs.md)
- [ADR Index](adr/README.md)
- [Observability Playbook (Lite)](runbooks/observability_playbook_lite.md)
- [Safety & Guardrails](safety-and-guardrails.md)
- [Evaluation](evaluation.md)
- [Deployment](deployment.md)

## Suggested Reading Paths

### New contributors
1. [Architecture](architecture.md)
2. [Safety & Guardrails](safety-and-guardrails.md)
3. [Evaluation](evaluation.md)

### Operators / platform engineers
1. [Deployment](deployment.md)
2. [Safety & Guardrails](safety-and-guardrails.md)
3. [Evaluation](evaluation.md)

## Repository Conventions (summary)

- Keep changes small and reversible.
- Validate all external input at boundaries.
- Preserve typed interfaces and structured outputs.
- Prefer test-first workflows where practical.
- Avoid secrets and unsafe shell/database patterns.

For contribution process details, see `CONTRIBUTING.md`.