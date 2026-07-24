# ADR-004: Refusal on Weak Evidence

## Status

Accepted

## Context

The repository is a demonstration implementation of clinical-document RAG controls. In this context, answering when evidence is weak increases the risk of presenting unsupported conclusions. The system already includes retrieval confidence scoring and risk-level-aware thresholds, but the key review question is policy behavior when retrieved evidence is not strong enough.

The design objective is to favor explicit refusal or clarification over speculative answers.

## Decision

The query path will refuse or withhold direct answers when evidence is missing or weak.

Operationally, this is implemented by:

- classifying evidence status (`missing`, `weak`, `sufficient`) from retrieval outcomes
- applying risk-aware similarity thresholds from governance rules
- routing weak/missing evidence to non-answer safety actions (`insufficient_evidence` or `refuse`)
- preserving decision metadata in query responses and audit records

Primary implementation references:

- [backend/refusal/logic.py](../../backend/refusal/logic.py)
- [backend/services/query_service.py](../../backend/services/query_service.py)
- [backend/safety/decision_engine.py](../../backend/safety/decision_engine.py)
- [backend/safety/policy.py](../../backend/safety/policy.py)

## Alternatives Considered

1. Always answer with confidence disclaimers
- Rejected because disclaimers alone do not prevent unsupported outputs.

2. Lower refusal thresholds for a higher answer rate
- Rejected because this undermines evidence-grounding discipline in the repository objective.

3. Human review for every query
- Rejected for baseline workflow due to high operational overhead and reduced usability for local demo runs.

## Consequences

Positive:

- More conservative and reviewable behavior when evidence is weak.
- Clear safety decision paths for automated tests and evaluation harnesses.
- Better alignment between retrieval quality and answer eligibility.

Trade-offs:

- More refusal or clarification responses in ambiguous queries.
- Lower apparent answer coverage in exchange for stronger grounding discipline.
- Threshold tuning remains an engineering trade-off and requires documented evaluation updates.

## Scope and Non-Claims

This ADR documents engineering decision-making and safety posture. It is not clinical validation, not a medical efficacy claim, and not evidence of medical-device readiness.
