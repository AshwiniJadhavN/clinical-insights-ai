"""Build an integration-test relationship graph for human review."""

from __future__ import annotations

from backend.testing_ai.models import CoverageAnalysisResult


class IntegrationGraphBuilder:
    """Create a Mermaid graph that explains testing traceability and coverage."""

    def build(self, coverage: CoverageAnalysisResult) -> str:
        score_lookup = {score.category: score.score_percent for score in coverage.risk_coverage_scores}
        high_risk_gaps = [gap.title for gap in coverage.coverage_gaps if gap.risk_level == "high" and gap.status != "covered"]
        unresolved_gaps = " | ".join(high_risk_gaps[:3]) if high_risk_gaps else "No uncovered high-risk gaps inferred"
        return (
            "flowchart TD\n"
            "    subgraph Traceability[Traceability Graph]\n"
            "        Requirement[Requirement] --> Risk[Risk]\n"
            "        Risk --> IntegrationTest[Integration Test]\n"
            "        IntegrationTest --> CIPipeline[CI Pipeline]\n"
            "        CIPipeline --> Result[Result]\n"
            "        Result --> AuditEvidence[Audit Evidence]\n"
            "    end\n"
            "    subgraph RuntimePath[Runtime Integration Path]\n"
            f"        API[API] -->|Evidence Retrieval {score_lookup.get('Evidence Retrieval', 0)}%| Retriever[Retriever]\n"
            "        Retriever --> PromptBuilder[Prompt Builder]\n"
            f"        PromptBuilder -->|Prompt Injection {score_lookup.get('Prompt Injection', 0)}%| LLM[LLM]\n"
            f"        LLM -->|Safety Rules {score_lookup.get('Safety Rules', 0)}%| Governance[Governance]\n"
            f"        Governance -->|Audit Logging {score_lookup.get('Audit Logging', 0)}%| Audit[Audit]\n"
            "        Audit --> Response[Response]\n"
            "    end\n"
            f"    FailureRecovery[Failure Recovery {score_lookup.get('Failure Recovery', 0)}%] --> CIPipeline\n"
            f"    Configuration[Configuration {score_lookup.get('Configuration', 0)}%] --> API\n"
            f"    Gaps[High-Risk Gaps: {unresolved_gaps}] --> IntegrationTest\n"
        )