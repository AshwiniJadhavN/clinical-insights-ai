# Failure Modes (Production Readiness Review)

Date: 2026-07-08

This document records realistic failure scenarios for the current implementation.
It is intentionally implementation-first: what the code does today, what mitigations exist, and what still needs work.

Scope:
- Query pipeline (`/ask`, `/query`)
- Document ingestion (`/documents/upload`)
- Startup and deployment paths
- Audit and traceability paths

Out of scope:
- Regulatory certification
- Full clinical risk management file
- Cloud-provider specific operations playbooks

## Failure Mode Matrix

| Failure scenario | Trigger | Current behavior | Current mitigation | Current limitation | Future improvement |
|---|---|---|---|---|---|
| Empty vector database | No documents indexed, or vector store is empty | Query returns an insufficient-evidence path; answer generation is skipped or returns no-context behavior | Safety decision path and retrieval checks avoid unsupported answer generation | User still receives a generic non-diagnostic message; no guided remediation in API response | Add explicit machine-readable failure reason and remediation guidance (for UI and runbooks) |
| Missing evidence in retrieved chunks | Retrieval returns chunks but below threshold / incomplete support | Response is refused, clarified, or marked insufficient evidence depending on decision path | `evaluate_retrieval` + `compute_confidence` + safety decision engine gate generation | Confidence is heuristic and can miss semantic edge cases | Add offline retrieval quality regression suite with domain-specific acceptance thresholds |
| LLM unavailable at startup/configuration time | Missing API key or provider init error | API falls back to `FakeGenerator` for non-mock path in dependency wiring | Runtime continues without crashing; explicit log warning emitted | Fallback can hide provider outage in environments that expected a real model | Add explicit "provider_mode" field in health/query metadata and fail-fast option for non-demo environments |
| LLM timeout during generation | Provider/network latency exceeds `llm_timeout_seconds` | Query is turned into a timeout refusal decision; no partial answer returned | `asyncio.wait_for` timeout + safety timeout decision | No retry/backoff policy; no provider circuit breaker | Add bounded retry policy and provider health backoff metrics |
| Retrieval backend unavailable at query time | Retriever singleton not initialized, backend unavailable | Endpoint returns HTTP 503 ("Vector store is not ready") | Dependency guards in API layer prevent unsafe execution | 503 does not distinguish initialization failure vs transient backend failure | Return structured error codes and map to operations runbook actions |
| Embedding model load failure | Invalid embedding model name or missing dependency/model assets | Startup raises runtime error for embedder initialization (except mock mode path) | Fail-fast embedder initialization in bootstrap | Local path behavior differs under `MOCK_LLM=true`, which can mask embedding issues | Add startup self-test endpoint and CI boot checks with `MOCK_LLM=false` profile |
| Embedding model changes without re-indexing | `embedding_model` is changed while existing vectors remain from prior model | Retrieval quality may degrade silently; system still serves answers from mixed-history vectors | None beyond operator discipline and manual reindex workflows | No embedding-version stamp attached to chunks/documents in active retrieval path | Add embedding model + dimension metadata per indexed chunk and enforce incompatibility checks |
| Chunk size/overlap changes without re-indexing | `chunk_size`/`chunk_overlap` changed for new uploads only | Corpus becomes mixed granularity; retrieval ranking/citations can drift | None beyond manual reingestion | No chunking-version metadata or migration marker in vector records | Add chunking profile version and reindex requirement checks before accepting mixed corpora |
| Database unavailable at startup | PostgreSQL unavailable in local/prod-like startup | In non-`PG_ONLY` mode startup logs warning and continues with degraded behavior; in `PG_ONLY` mode startup fails | Graceful fallback design in bootstrap for non-strict mode | Query audit logging can be disabled silently from end-user perspective | Add explicit degraded-mode health status and startup banner with blocked capabilities |
| Audit database write failure | SQL audit insert fails at runtime | Query request still succeeds; audit write failure is logged only | `AuditService.log_query()` catches exceptions and never raises | Loss of query audit event is possible; no dead-letter queue/retry | Add asynchronous retry buffer/dead-letter path for audit writes |
| Docker Compose startup failure | DB healthcheck fails, port collisions, missing local resources | API container may not start or may stay unhealthy depending on dependency state | Compose healthchecks and restart policy | Failure reason discovery depends on container logs; no one-command diagnosis output | Add scripted preflight (`ports`, `disk`, env validation) and troubleshooting command in docs |
| Upload parse failure (invalid/corrupt PDFs) | Parser cannot extract text or file is corrupted | Document status becomes `error`; no indexing is performed | Parser exceptions mapped to safe user-facing error message and warnings | OCR is not supported; scanned PDFs frequently produce little/no text | Add optional OCR ingestion path behind feature flag |
| Upload policy violation | Unsupported extension, empty file, oversized file | Upload is rejected with HTTP 422 validation error | `validate_upload()` enforces extension and size constraints | MIME-type validation is extension-based today (not deep file signature inspection) | Add content-type sniffing and file-signature verification before parse |
| Citation mismatch or missing citations | Generated citations do not map to retrieved evidence | Safety layer refuses output instead of returning unsupported answer | Citation verifier in safety decision path | Refusal reason granularity is limited for clients | Add machine-readable refusal taxonomy and operator dashboards |
| Contradictory evidence | Retrieved chunks contain conflicting signals | Safety layer can move to clarify path instead of direct answer | Safety policy and evidence checks | Contradiction logic is heuristic and may not capture all conflict patterns | Add explicit contradiction detection tests and richer conflict metadata |
| Governance rule block for advisory draft | `/agentic/draft` request violates governance rule | API returns HTTP 400 with audit id; action is logged to JSONL trail | Governance rule engine + JSONL audit writer | Block context is limited to available metadata fields | Add richer governance decision payload and reviewer workflow linkage |
| Audit search access denied unexpectedly | Internal-network or API-key checks fail | `/audit/search` returns HTTP 403 | Access control in audit search endpoint | Operational ambiguity (credential issue vs network policy) | Add explicit auth mode in response headers and ops documentation |

## Cross-Cutting Constraints and Honest Limits

- Confidence score is a retrieval heuristic, not a calibrated probability of correctness.
- Query SQL audit and JSONL advisory audit are separate stores with different schemas and guarantees.
- Current traceability is useful for review, but full deterministic replay is not implemented.
- Uploaded source files may contain PHI/PII and are stored in local volume paths unless external storage controls are introduced.
- Mock and fallback modes improve demo reliability but can conceal production-only failure classes.

## Recommended Order of Hardening (Non-Breaking)

1. Add explicit degraded-mode signals in health endpoints and docs.
2. Add embedding/chunking version metadata and reindex checks.
3. Add structured failure reason codes for query refusal and 503 scenarios.
4. Add audit-write retry/dead-letter behavior.
5. Add preflight checks for Docker/local runtime startup.
