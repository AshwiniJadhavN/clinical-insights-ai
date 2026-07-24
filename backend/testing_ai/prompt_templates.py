"""Prompt-style templates and deterministic scenario catalogue.

The current implementation uses deterministic heuristics to keep the portfolio
project runnable without external LLM dependencies. These templates document the
intended AI contract and provide structured scenario metadata.
"""

from __future__ import annotations

from typing import Final, Literal, TypedDict


class ScenarioCatalogueItem(TypedDict):
    title: str
    requirement: str
    system_behavior: str
    risk: str
    expected_result: str
    evidence_to_collect: list[str]
    tags: list[str]
    related_endpoints: list[str]
    risk_level: Literal["low", "medium", "high"]


class FailurePatternItem(TypedDict):
    pattern: str
    summary: str
    component: str
    fix: str
    steps: list[str]


class RiskCoverageCategoryItem(TypedDict):
    category: str
    tags: list[str]

HUMAN_REVIEW_DISCLAIMER: Final[str] = (
    "AI-generated integration testing output is advisory only and requires "
    "human review before use, approval, or execution."
)

GENERATED_TEST_BANNER: Final[str] = (
    '"""AI-generated pytest integration test draft.\n\n'
    "REQUIRES HUMAN REVIEW BEFORE EXECUTION OR APPROVAL.\n"
    "This file is advisory only and must be validated by an engineer before it "
    "is renamed, enabled, or executed in CI.\n"
    '"""'
)

SCENARIO_CATALOGUE: Final[list[ScenarioCatalogueItem]] = [
    {
        "title": "Evidence retrieval succeeds but generation fails",
        "requirement": "The query pipeline should surface a safe upstream failure when the generator fails after evidence retrieval.",
        "system_behavior": "Retriever returns evidence and the generator raises an exception or timeout.",
        "risk": "Users receive silent failure, partial answers, or missing error telemetry.",
        "expected_result": "The API returns a controlled 502 response and preserves evidence-oriented observability.",
        "evidence_to_collect": ["query response payload", "application error log", "audit record"],
        "tags": ["query", "generator", "retrieval", "error-handling"],
        "related_endpoints": ["/query"],
        "risk_level": "high",
    },
    {
        "title": "Generation succeeds without supporting evidence",
        "requirement": "The safety layer should block unsupported answers when evidence is missing.",
        "system_behavior": "Generator returns answer text while citations are empty or invalid.",
        "risk": "Hallucinated clinical content appears trustworthy without evidence.",
        "expected_result": "The response is refused or marked insufficient evidence with review metadata.",
        "evidence_to_collect": ["response JSON", "citation list", "safety decision metadata"],
        "tags": ["query", "citations", "safety", "evidence"],
        "related_endpoints": ["/query"],
        "risk_level": "high",
    },
    {
        "title": "Weak evidence should trigger refusal",
        "requirement": "Weak evidence must not produce a confident answer.",
        "system_behavior": "Retriever returns low-confidence evidence below configured threshold.",
        "risk": "Low-signal evidence creates overconfident responses.",
        "expected_result": "The system refuses or asks for clarification and records the refusal reason.",
        "evidence_to_collect": ["confidence score", "refusal reason", "audit log"],
        "tags": ["query", "safety", "confidence", "refusal"],
        "related_endpoints": ["/query"],
        "risk_level": "high",
    },
    {
        "title": "Audit logging unavailable",
        "requirement": "Clinical operations should degrade safely when audit logging storage is unavailable.",
        "system_behavior": "Audit persistence raises an exception during request handling.",
        "risk": "Traceability is lost without a clear operator signal.",
        "expected_result": "The request remains safe, the failure is visible, and human review is flagged.",
        "evidence_to_collect": ["application log", "operator alert", "response metadata"],
        "tags": ["audit", "logging", "resilience"],
        "related_endpoints": ["/query", "/audit/search"],
        "risk_level": "high",
    },
    {
        "title": "Database unavailable",
        "requirement": "Database outages should produce deterministic readiness and request behavior.",
        "system_behavior": "Database session initialization or query execution fails.",
        "risk": "The API may appear healthy while persistence-backed features are broken.",
        "expected_result": "Readiness or affected request paths fail with a controlled message and logs.",
        "evidence_to_collect": ["health output", "readiness output", "database error log"],
        "tags": ["database", "health", "readiness"],
        "related_endpoints": ["/health", "/health/ready", "/query"],
        "risk_level": "high",
    },
    {
        "title": "Vector database timeout",
        "requirement": "Vector retrieval timeouts should not produce misleading answers.",
        "system_behavior": "Vector store request times out during retrieval.",
        "risk": "The API may return empty or fabricated evidence without explicit failure.",
        "expected_result": "The request fails safely or returns insufficient evidence with timeout telemetry.",
        "evidence_to_collect": ["timeout log", "response detail", "retrieval metrics"],
        "tags": ["vector", "retrieval", "timeout"],
        "related_endpoints": ["/query", "/health"],
        "risk_level": "high",
    },
    {
        "title": "Invalid document metadata",
        "requirement": "Document ingestion should reject invalid metadata before indexing.",
        "system_behavior": "Metadata fields are missing, malformed, or inconsistent with schema rules.",
        "risk": "Corrupted metadata can poison retrieval and traceability.",
        "expected_result": "Upload or indexing is rejected with a safe validation response.",
        "evidence_to_collect": ["validation response", "schema error", "audit trail"],
        "tags": ["documents", "validation", "metadata"],
        "related_endpoints": ["/documents"],
        "risk_level": "medium",
    },
    {
        "title": "Malformed uploaded document",
        "requirement": "Malformed files must be rejected before processing.",
        "system_behavior": "Uploaded file has invalid format, content, or parser failure.",
        "risk": "Parser exceptions can crash upload flows or create unsafe ingestion artifacts.",
        "expected_result": "The API returns a safe validation error and logs the parsing failure.",
        "evidence_to_collect": ["upload response", "parser log", "file validation event"],
        "tags": ["documents", "upload", "parser"],
        "related_endpoints": ["/documents"],
        "risk_level": "high",
    },
    {
        "title": "Configuration mismatch",
        "requirement": "Configuration drift should be visible before runtime behavior diverges.",
        "system_behavior": "Environment and YAML-backed settings disagree about provider or backend settings.",
        "risk": "The system starts with an unexpected model or vector backend.",
        "expected_result": "Startup or diagnostic tooling identifies the mismatch and recommends correction.",
        "evidence_to_collect": ["settings snapshot", "startup log", "diagnostic report"],
        "tags": ["config", "startup", "governance"],
        "related_endpoints": ["/health", "/testing-ai/report"],
        "risk_level": "medium",
    },
    {
        "title": "Missing environment variables",
        "requirement": "Missing required settings should fail fast with a clear error.",
        "system_behavior": "Required environment variables for database or provider credentials are absent.",
        "risk": "The service runs in a partially configured state.",
        "expected_result": "Startup or CI catches the misconfiguration before production traffic is served.",
        "evidence_to_collect": ["startup output", "configuration validation error", "CI log"],
        "tags": ["config", "environment", "startup"],
        "related_endpoints": ["/health/ready"],
        "risk_level": "high",
    },
    {
        "title": "Health endpoint failures",
        "requirement": "Health endpoints should accurately report subsystem readiness.",
        "system_behavior": "A dependency is unavailable but health output remains healthy or incomplete.",
        "risk": "Orchestrators route traffic to an unhealthy instance.",
        "expected_result": "Health or readiness endpoints reflect the failing subsystem accurately.",
        "evidence_to_collect": ["health JSON", "dependency status", "orchestrator event"],
        "tags": ["health", "readiness", "observability"],
        "related_endpoints": ["/health", "/health/live", "/health/ready"],
        "risk_level": "high",
    },
    {
        "title": "Metrics endpoint unavailable",
        "requirement": "Operational metrics should remain accessible or fail visibly.",
        "system_behavior": "Metrics handler raises or returns invalid Prometheus content.",
        "risk": "Monitoring blind spots hide production degradation.",
        "expected_result": "The endpoint returns valid metrics output or a controlled operator-visible failure.",
        "evidence_to_collect": ["metrics response", "scrape log", "application log"],
        "tags": ["metrics", "observability"],
        "related_endpoints": ["/metrics"],
        "risk_level": "medium",
    },
    {
        "title": "Incorrect citation generation",
        "requirement": "Citations must align with retrieved evidence.",
        "system_behavior": "Generated citations reference missing documents, bad chunk indexes, or mismatched excerpts.",
        "risk": "Reviewers trust invalid evidence trails.",
        "expected_result": "Citation verification or tests catch the mismatch before approval.",
        "evidence_to_collect": ["citation payload", "retrieved chunk", "verification output"],
        "tags": ["citations", "query", "evidence"],
        "related_endpoints": ["/query"],
        "risk_level": "high",
    },
    {
        "title": "Empty retrieval results",
        "requirement": "Empty retrieval should not be presented as a successful clinical answer.",
        "system_behavior": "Retriever returns zero chunks for a normal query.",
        "risk": "The generator may hallucinate an answer without evidence.",
        "expected_result": "The system refuses, clarifies, or reports insufficient evidence.",
        "evidence_to_collect": ["retrieval count", "response JSON", "audit record"],
        "tags": ["retrieval", "query", "empty-result"],
        "related_endpoints": ["/query"],
        "risk_level": "high",
    },
    {
        "title": "Prompt injection attempts",
        "requirement": "Prompt injection must be blocked before model execution.",
        "system_behavior": "A query contains known prompt injection phrases or hostile instructions.",
        "risk": "Safety policies are bypassed and unsafe output is generated.",
        "expected_result": "The request is blocked with a 422 response and safety metadata.",
        "evidence_to_collect": ["request payload", "guardrail decision", "response detail"],
        "tags": ["security", "prompt-injection", "safety"],
        "related_endpoints": ["/query", "/advisory/draft"],
        "risk_level": "high",
    },
    {
        "title": "Safety policy violations",
        "requirement": "Unsafe output must be refused consistently.",
        "system_behavior": "Generated output breaches configured safety policies or refusal logic.",
        "risk": "Unsafe clinical content leaves the boundary unchecked.",
        "expected_result": "The system returns a refusal path and records the policy reason.",
        "evidence_to_collect": ["safety decision", "response JSON", "policy log"],
        "tags": ["safety", "policy", "refusal"],
        "related_endpoints": ["/query"],
        "risk_level": "high",
    },
    {
        "title": "Rate limiting",
        "requirement": "Repeated requests should respect rate-limit controls.",
        "system_behavior": "A caller exceeds the configured request window.",
        "risk": "The service becomes unstable or protection controls are bypassed.",
        "expected_result": "The middleware returns a controlled throttling response.",
        "evidence_to_collect": ["response status", "rate-limit headers", "middleware log"],
        "tags": ["security", "rate-limit", "middleware"],
        "related_endpoints": ["/query", "/health", "/testing-ai/generate-tests"],
        "risk_level": "medium",
    },
    {
        "title": "Concurrent requests",
        "requirement": "Concurrent calls should preserve request identifiers and safe isolation.",
        "system_behavior": "Multiple requests arrive simultaneously under mixed dependencies.",
        "risk": "Correlation IDs, metrics, or shared state become inconsistent.",
        "expected_result": "Each request returns a distinct correlation ID and consistent metrics behavior.",
        "evidence_to_collect": ["response headers", "metrics snapshot", "application log"],
        "tags": ["concurrency", "middleware", "observability"],
        "related_endpoints": ["/query", "/health", "/metrics"],
        "risk_level": "medium",
    },
    {
        "title": "Large document uploads",
        "requirement": "Oversized uploads should be rejected safely.",
        "system_behavior": "Uploaded file exceeds configured size limit.",
        "risk": "The API may exhaust resources or accept non-compliant content.",
        "expected_result": "The upload is rejected with a safe validation response and no indexing occurs.",
        "evidence_to_collect": ["upload response", "size validation log", "storage state"],
        "tags": ["documents", "upload", "size-limit"],
        "related_endpoints": ["/documents"],
        "risk_level": "medium",
    },
]

FAILURE_PATTERNS: Final[list[FailurePatternItem]] = [
    {
        "pattern": "validationerror",
        "summary": "Schema validation failed during integration flow.",
        "component": "pydantic_schema_validation",
        "fix": "Review the request or response schema for missing or incompatible fields.",
        "steps": [
            "Compare the failing payload against the expected Pydantic model.",
            "Check recent changes to response_model declarations.",
        ],
    },
    {
        "pattern": "timeout",
        "summary": "A dependency timed out during the integration flow.",
        "component": "timeout_or_network_dependency",
        "fix": "Check dependency availability, configured timeouts, and retry behavior.",
        "steps": [
            "Identify whether the timeout came from retrieval, database, or the LLM provider.",
            "Inspect latency metrics and related logs around the failure timestamp.",
        ],
    },
    {
        "pattern": "connection refused",
        "summary": "A backing service was unreachable.",
        "component": "service_connectivity",
        "fix": "Verify the target host, port, and service startup ordering.",
        "steps": [
            "Check docker-compose or CI service containers for startup failures.",
            "Confirm the configured endpoint matches the running dependency.",
        ],
    },
    {
        "pattern": "assertionerror",
        "summary": "An integration assertion no longer matches observed behavior.",
        "component": "integration_test_expectation",
        "fix": "Review the failing assertion against current API behavior and recent code changes.",
        "steps": [
            "Find the first failing assertion in pytest output.",
            "Check whether the behavior change is intended or a regression.",
        ],
    },
    {
        "pattern": "503",
        "summary": "A readiness or dependency-availability failure surfaced through the API.",
        "component": "service_readiness_or_dependency",
        "fix": "Inspect startup initialization, dependency readiness, and fallback behavior.",
        "steps": [
            "Verify database, retriever, and embedder readiness.",
            "Check whether mock or fallback settings were expected in this environment.",
        ],
    },
    {
        "pattern": "rate limit",
        "summary": "Rate-limiting behavior triggered during test execution.",
        "component": "rate_limit_middleware",
        "fix": "Adjust test pacing or configure explicit rate-limit test fixtures.",
        "steps": [
            "Inspect request frequency and client identity in the test.",
            "Confirm the middleware window and request-count settings.",
        ],
    },
]

RISK_COVERAGE_CATEGORIES: Final[list[RiskCoverageCategoryItem]] = [
    {
        "category": "Evidence Retrieval",
        "tags": ["retrieval", "vector", "citations", "evidence", "empty-result"],
    },
    {
        "category": "Safety Rules",
        "tags": ["safety", "refusal", "policy", "confidence"],
    },
    {
        "category": "Audit Logging",
        "tags": ["audit", "logging", "observability"],
    },
    {
        "category": "Failure Recovery",
        "tags": ["timeout", "error-handling", "resilience", "database"],
    },
    {
        "category": "Configuration",
        "tags": ["config", "environment", "startup", "governance"],
    },
    {
        "category": "Document Ingestion",
        "tags": ["documents", "upload", "parser", "metadata", "validation", "size-limit"],
    },
    {
        "category": "Prompt Injection",
        "tags": ["prompt-injection", "security", "rate-limit", "middleware"],
    },
]