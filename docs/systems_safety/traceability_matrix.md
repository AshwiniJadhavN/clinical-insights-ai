# Traceability Matrix

| Hazard | Safety Requirement | Implementation | Test Case |
|---|---|---|---|
| HAZ-001 Unsupported medical conclusion | SR-001 | `backend/safety/output_validation.py` | `tests/safety/test_decision_engine.py` |
| HAZ-002 Fabricated citation | SR-002 | `backend/safety/citation_verifier.py` | `tests/safety/test_decision_engine.py` |
| HAZ-003 Missing evidence | SR-003 | `backend/safety/evidence_validation.py`, `backend/services/query_service.py` | `tests/safety/test_decision_engine.py` |
| HAZ-004 Low confidence retrieval | SR-004 | `backend/refusal/logic.py`, `backend/safety/evidence_validation.py` | `tests/domains/refusal/test_refusal_logic.py` |
| HAZ-005 Prompt injection | SR-006 | `backend/safety/prompt_injection.py`, `backend/guardrails/safety_checker.py` | `tests/domains/refusal/test_guardrails.py` |
| HAZ-006 Prompt leakage | SR-007 | `backend/safety/output_validation.py` | `tests/safety/test_decision_engine.py` |
| HAZ-007 Contradictory evidence | SR-010 | `backend/safety/evidence_validation.py`, `backend/safety/policy.py` | `tests/safety/test_decision_engine.py` |
| HAZ-008 Corrupted metadata | SR-009 | `backend/safety/evidence_validation.py` | `tests/safety/test_decision_engine.py` |
| HAZ-009 Generation timeout | SR-008 | `backend/services/query_service.py` | `tests/services/test_query_service.py` |
| HAZ-010 Missing reviewer oversight | SR-012 | `backend/api/review.py`, `backend/services/review_service.py` | `tests/services/test_review_service.py` |