# Verification Strategy

## Verification Objectives

- Prove the safety layer blocks unsupported answers before they reach users.
- Prove retrieval weakness, metadata corruption, and citation mismatch are handled deterministically.
- Prove human-review decisions are append-only and auditable.
- Prove security controls degrade safely under missing auth, prompt injection, and rate pressure.

## Test Strategy

| Verification area | Method | Evidence |
|---|---|---|
| Hallucination prevention | Unit test | `tests/services/test_query_service.py` |
| Missing evidence | Unit test | `tests/safety/test_decision_engine.py` |
| Empty vector search | Unit test | `tests/safety/test_decision_engine.py` |
| Timeout handling | Unit test with fault injection | `tests/services/test_query_service.py` |
| Prompt injection | Guardrail test | `tests/domains/refusal/test_guardrails.py` |
| Malformed documents / metadata corruption | Safety validator test | `tests/safety/test_decision_engine.py` |
| Contradictory documents | Safety validator test | `tests/safety/test_decision_engine.py` |
| Citation mismatch | Output validation test | `tests/safety/test_decision_engine.py` |
| Confidence threshold behavior | Refusal logic test | `tests/domains/refusal/test_refusal_logic.py` |
| Human review persistence | Service test | `tests/services/test_review_service.py` |

## Release Gate Expectations

- Ruff and pytest remain CI gates.
- Dependency audit and Trivy image scanning remain active in GitHub Actions.
- Architecture gate now checks for safety architecture and traceability documentation.