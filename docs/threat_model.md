# Threat Model

## Assets

- Clinical document text
- Embeddings and vector indexes
- Audit records
- API keys and deployment credentials
- Governance rules

## Key Threats

- Prompt injection attempts to bypass safety controls
- Unsupported clinical answers presented as authoritative
- Vector-store divergence between ChromaDB and PGVector
- Tampering with audit logs
- Secret leakage in repository or CI
- Unauthorized access to `/audit/search`
- Deployment of an unhealthy service during cold start

## Controls

- Input guardrails and canary tests
- Evidence-bound generation and refusal thresholds
- Risk-based YAML similarity rules
- Vector reconciliation CLI
- Tamper-evident JSONL hash chains
- Gitleaks and dependency scanning
- API-key or internal-network protection for audit search
- Split liveness and readiness probes

## Residual Risks

- Similarity score is not clinical truth.
- Demo sample data is too small for clinical validity.
- JSONL audit hash chains are tamper-evident, not immutable storage.
- Terraform/Kubernetes artifacts are reference implementations.

## Threat Model Refresh

### Threats and Controls

| Threat | Control |
|---|---|
| Prompt injection and jailbreak attempts | `PromptInjectionDetector`, `SafetyChecker`, deterministic refusal |
| Fabricated or mismatched citations | `CitationVerifier` |
| Weak retrieval presented as fact | `EvidenceValidator`, refusal thresholds, `SafetyPolicyEnforcer` |
| Output containing hidden prompt material | `OutputValidator` |
| Excessive request volume | `RateLimitMiddleware` |
| Unauthenticated API use in protected deployments | `AuthenticationMiddleware` with `X-API-Key` |
| Undetected reviewer override | Append-only `reviewer_decisions.jsonl` audit trail |

### Security Engineering Notes

- Secrets remain environment-managed through `pydantic-settings`.
- Dependency and image scanning remain part of CI.
- Safety and security logic are separated from business logic to improve reviewability and regression isolation.
