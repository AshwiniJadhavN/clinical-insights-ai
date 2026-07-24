# Failure Modes

| Failure mode | Detection | Fail-safe behaviour | Recovery |
|---|---|---|---|
| Prompt injection detected | Input guardrails and prompt injection detector | HTTP 422 or safety refusal | Rephrase query |
| No evidence retrieved | Evidence validator | `insufficient_evidence` response | Upload relevant documents |
| Weak retrieval | Confidence threshold rule | `insufficient_evidence` response | Ask narrower question or add source material |
| Contradictory evidence | Contradiction heuristic | `clarify` response | Human reviewer adjudication |
| Citation mismatch | Citation verifier | `refuse` response | Investigate generator output or metadata integrity |
| Output unsupported by evidence | Output validator | `refuse` response | Improve prompt, retrieval quality, or evidence set |
| LLM timeout | Timeout wrapper in `QueryService` | `refuse` response | Retry or investigate provider health |
| Corrupted metadata | Evidence validator | `refuse` response | Re-index documents and repair ingestion pipeline |
| Human reviewer rejects output | Review decision API | Append-only audit record | Query can be retried with revised evidence scope |