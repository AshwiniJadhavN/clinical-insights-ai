"""Markdown report generation for integration coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.testing_ai.graph_builder import IntegrationGraphBuilder
from backend.testing_ai.models import CoverageAnalysisResult, GeneratedTestFile
from backend.testing_ai.prompt_templates import HUMAN_REVIEW_DISCLAIMER


class ReportGenerator:
    """Write a deterministic markdown report for human review."""

    def __init__(self) -> None:
        self._graph_builder = IntegrationGraphBuilder()

    def generate(
        self,
        report_directory: Path,
        coverage: CoverageAnalysisResult,
        generated_tests: list[GeneratedTestFile],
    ) -> tuple[Path, Path, str, str, list[str]]:
        report_directory.mkdir(parents=True, exist_ok=True)
        recommendations = self._recommendations(coverage, generated_tests)
        integration_graph = self._graph_builder.build(coverage)
        markdown = self._build_markdown(coverage, generated_tests, integration_graph, recommendations)
        report_path = report_directory / "ai_assisted_integration_report.md"
        graph_path = report_directory / "integration_test_graph.mmd"
        report_path.write_text(markdown, encoding="utf-8")
        graph_path.write_text(integration_graph, encoding="utf-8")
        return report_path, graph_path, markdown, integration_graph, recommendations

    def _build_markdown(
        self,
        coverage: CoverageAnalysisResult,
        generated_tests: list[GeneratedTestFile],
        integration_graph: str,
        recommendations: list[str],
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        missing_scenarios = [gap for gap in coverage.coverage_gaps if gap.status != "covered"]
        high_risk_gaps = [gap for gap in coverage.coverage_gaps if gap.risk_level == "high" and gap.status != "covered"]
        score_section = "\n".join(
            f"- {score.category}\n  {score.bar} {score.score_percent}% ({score.covered_scenarios} covered, {score.partial_scenarios} partial, {score.missing_scenarios} missing)"
            for score in coverage.risk_coverage_scores
        ) or "- No risk coverage scores available."
        generated_section = "\n".join(
            f"- {entry.title}: {entry.path}"
            for entry in generated_tests
        ) or "- No generated draft tests were produced in this run."
        missing_section = "\n".join(
            f"- {gap.title} ({gap.risk_level.value}, {gap.status.value}): {gap.reason}"
            for gap in missing_scenarios
        ) or "- No missing scenarios inferred from current coverage signals."
        high_risk_section = "\n".join(
            f"- {gap.title}: {gap.reason}"
            for gap in high_risk_gaps
        ) or "- No uncovered high-risk gaps inferred."
        recommendation_section = "\n".join(f"- {item}" for item in recommendations)
        return (
            "# AI Assisted Integration Testing Report\n\n"
            f"> {HUMAN_REVIEW_DISCLAIMER}\n\n"
            f"Generated at: {timestamp}\n\n"
            "## Current Integration Coverage\n\n"
            f"- Total endpoints discovered: {coverage.summary.total_endpoints}\n"
            f"- Endpoints with test signals: {coverage.summary.endpoints_with_test_signals}\n"
            f"- Endpoint coverage ratio: {coverage.summary.coverage_ratio}\n"
            f"- High-risk scenarios covered: {coverage.summary.covered_high_risk_scenarios}/{coverage.summary.total_high_risk_scenarios}\n"
            f"- High-risk gap ratio: {coverage.summary.high_risk_gap_ratio}\n\n"
            "## Risk Coverage Score\n\n"
            f"{score_section}\n\n"
            "## Integration Test Graph\n\n"
            "```mermaid\n"
            f"{integration_graph}"
            "```\n\n"
            "## Missing Scenarios\n\n"
            f"{missing_section}\n\n"
            "## Generated Tests\n\n"
            f"{generated_section}\n\n"
            "## High-Risk Gaps\n\n"
            f"{high_risk_section}\n\n"
            "## Recommendations\n\n"
            f"{recommendation_section}\n"
        )

    def _recommendations(
        self,
        coverage: CoverageAnalysisResult,
        generated_tests: list[GeneratedTestFile],
    ) -> list[str]:
        recommendations = []
        if coverage.summary.high_risk_gap_ratio > 0.4:
            recommendations.append(
                "Prioritize high-risk refusal, evidence, and dependency-failure scenarios before expanding lower-risk coverage."
            )
        if not generated_tests:
            recommendations.append(
                "Generate draft pytest templates for uncovered high-risk scenarios and review them manually before adoption."
            )
        recommendations.append(
            "Correlate generated scenarios with audit and CI evidence before promoting them into executable test suites."
        )
        recommendations.append(
            "Keep generated drafts under human review and do not auto-approve AI-authored tests in CI."
        )
        return recommendations