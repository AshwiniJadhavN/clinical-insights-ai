# ADR 0004: Risk-Based Refusal Thresholds

## Status

Accepted

## Context

A single similarity threshold is too blunt for clinical content. Higher-risk
domains such as oncology or pediatric content should require stronger evidence.

## Decision

Assign each retrieved chunk a `risk_level` metadata value and evaluate YAML
similarity-threshold rules before calling the LLM.

Current thresholds:

- `HIGH`: `0.92`
- `MEDIUM`: `0.80`
- `LOW`: `0.65`

## Consequences

The platform fails closed for higher-risk evidence and can explain refusal
behavior through policy rather than hardcoded constants.
