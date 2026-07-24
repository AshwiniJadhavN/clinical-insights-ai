# Hazard Analysis

Clinical Insights AI is not a medical device, but this hazard analysis applies regulated-software discipline to foreseeable AI failure modes.

| Hazard | Cause | Potential impact | Initial risk | Risk control | Residual risk | Verification method |
|---|---|---|---|---|---|---|
| HAZ-001 Unsupported medical conclusion | LLM extrapolates beyond retrieved evidence | User trusts unsupported statement | High | RC-004 output validation and SafetyDecisionEngine refusal | Low | `tests/safety/test_decision_engine.py` and `tests/services/test_query_service.py` |
| HAZ-002 Fabricated citation | Model cites a document/chunk that was never retrieved | False traceability and unsafe trust | High | RC-002 citation verification | Low | `tests/safety/test_decision_engine.py` |
| HAZ-003 No evidence retrieved | Empty vector search or indexing gap | User receives unsupported answer | High | RC-001 evidence validation and deterministic insufficient-evidence response | Low | `tests/safety/test_decision_engine.py` |
| HAZ-004 Low-confidence retrieval | Similarity below configured threshold | Weak evidence accepted as strong evidence | High | RC-006 confidence threshold enforcement | Low | `tests/domains/refusal/test_refusal_logic.py` |
| HAZ-005 Prompt injection | User attempts instruction override | Safety controls bypassed | High | RC-005 prompt injection detection and input guardrails | Low | `tests/domains/refusal/test_guardrails.py` |
| HAZ-006 Prompt leakage | Model echoes system prompt or hidden instruction | Governance leakage and security loss | Medium | RC-004 output validation | Low | `tests/safety/test_decision_engine.py` |
| HAZ-007 Contradictory evidence | Retrieved chunks disagree on key measurements | System gives ambiguous advice without escalation | High | RC-003 clarification path via SafetyDecisionEngine | Medium | `tests/safety/test_decision_engine.py` |
| HAZ-008 Corrupted metadata | Missing doc id, filename, or invalid similarity metadata | Broken citations and audit trace | Medium | RC-002 metadata validation before answer | Low | `tests/safety/test_decision_engine.py` |
| HAZ-009 Timeout during generation | Provider or network delay | Partial or absent response without deterministic handling | Medium | RC-004 timeout-to-refusal behavior | Low | `tests/services/test_query_service.py` |
| HAZ-010 Human review omitted | High-risk output used without reviewer decision | Unsafe downstream use | Medium | RC-007 review decision API and audit trail | Low | `tests/services/test_review_service.py` |

## Risk Controls

- RC-001 Retrieval confidence validation in `backend/safety/evidence_validation.py`
- RC-002 Citation and metadata verification in `backend/safety/citation_verifier.py`
- RC-003 Clarification escalation for contradictory evidence in `backend/safety/evidence_validation.py`
- RC-004 Output validation and timeout refusal in `backend/safety/output_validation.py` and `backend/services/query_service.py`
- RC-005 Prompt injection detection in `backend/safety/prompt_injection.py`
- RC-006 Safety policy enforcement in `backend/safety/policy.py`
- RC-007 Human-in-the-loop review logging in `backend/api/review.py` and `backend/services/review_service.py`