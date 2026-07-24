# Clinical Validation Plan

This project does not perform clinical validation. This document describes what
would be required before a real healthcare use case.

## Validation Scope

- Define intended use and excluded use cases.
- Build a representative, de-identified evaluation set.
- Label expected evidence sources and acceptable answer boundaries.
- Measure retrieval recall, precision, false acceptance, and false refusal rates.
- Review generated answers with qualified clinicians.
- Track performance by risk category: `LOW`, `MEDIUM`, and `HIGH`.

## Required Metrics

- Retrieval recall@k
- Mean reciprocal rank
- Evidence sufficiency accuracy
- Unsafe answer rate
- Unsupported answer rate
- Refusal precision
- Refusal recall
- Human reviewer agreement

## Release Criteria

- No unsupported high-risk clinical answers in validation.
- High-risk content must meet stricter similarity thresholds.
- All answers must include source evidence.
- Audit trail must verify without hash-chain breaks.
- Canary adversarial tests must pass in CI.
