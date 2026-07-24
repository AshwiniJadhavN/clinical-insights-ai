# Safety Requirements

This document defines safety requirements, rationale, implementation, and verification hooks for the dedicated safety layer.

| Requirement | Rationale | Implementation | Unit test |
|---|---|---|---|
| SR-001 Never generate unsupported medical conclusions. | Mitigates hallucination and overclaim risk. | `backend/safety/output_validation.py` + `backend/safety/policy.py` | `tests/safety/test_decision_engine.py` |
| SR-002 Never fabricate citations. | Preserves evidence traceability and auditability. | `backend/safety/citation_verifier.py` | `tests/safety/test_decision_engine.py` |
| SR-003 Reject responses without retrieved evidence. | Prevents answer generation on empty retrieval. | `backend/safety/evidence_validation.py` | `tests/safety/test_decision_engine.py` |
| SR-004 Detect low confidence retrieval. | Prevents unsafe answers from weak retrieval. | `backend/refusal/logic.py` + `backend/safety/evidence_validation.py` | `tests/domains/refusal/test_refusal_logic.py` |
| SR-005 Ensure deterministic refusal behaviour. | Makes safety outcomes predictable, testable, and auditable. | `backend/safety/policy.py` | `tests/safety/test_decision_engine.py` |
| SR-006 Reject prompt injection attempts. | Stops instruction override and jailbreak attempts before retrieval/generation. | `backend/safety/prompt_injection.py` + `backend/guardrails/safety_checker.py` | `tests/domains/refusal/test_guardrails.py` |
| SR-007 Reject prompt leakage or system disclosure. | Protects governance and system prompts. | `backend/safety/output_validation.py` | `tests/safety/test_decision_engine.py` |
| SR-008 Fail safe on timeout. | Keeps service deterministic under provider degradation. | `backend/services/query_service.py` | `tests/services/test_query_service.py` |
| SR-009 Detect corrupted metadata. | Prevents broken citations and invalid risk evaluation. | `backend/safety/evidence_validation.py` | `tests/safety/test_decision_engine.py` |
| SR-010 Escalate contradictory evidence to clarification. | Avoids false certainty when documents disagree. | `backend/safety/evidence_validation.py` + `backend/safety/policy.py` | `tests/safety/test_decision_engine.py` |
| SR-011 Reject malformed or empty output. | Prevents unusable responses from entering downstream flows. | `backend/safety/output_validation.py` | `tests/safety/test_decision_engine.py` |
| SR-012 Support human review acceptance, modification, and rejection. | Adds operational oversight and post-AI governance. | `backend/api/review.py` + `backend/services/review_service.py` | `tests/services/test_review_service.py` |

## Systems Engineering Alignment

- IEC 62304 style separation of concerns: safety functions are isolated under `backend/safety/`.
- ISO 14971 style risk controls: each requirement maps to a named hazard and a verification artifact.
- ISO 15288 traceability: requirements flow into implementation, documentation, and tests.
- IEC 62366-1 style use risk handling: clarification and review reduce unsafe interpretation at the human interface.