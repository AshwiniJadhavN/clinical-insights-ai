"""Coverage analysis for advisory integration testing."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Iterable

from backend.testing_ai.models import (
    AdvisoryApprovalStatus,
    CoverageAnalysisResult,
    CoverageGap,
    CoverageStatus,
    CoverageSummary,
    EndpointContract,
    ExistingTestReference,
    RiskLevel,
    RiskCoverageScore,
)
from backend.testing_ai.prompt_templates import HUMAN_REVIEW_DISCLAIMER, RISK_COVERAGE_CATEGORIES, SCENARIO_CATALOGUE


class CoverageAnalyzer:
    """Infer current integration-test coverage from repository test files."""

    def analyze(
        self,
        project_root: Path,
        endpoints: list[EndpointContract],
    ) -> CoverageAnalysisResult:
        test_files = self._discover_test_files(project_root)
        endpoint_paths = [endpoint.path for endpoint in endpoints]
        existing_tests = [self._build_test_reference(path, endpoint_paths) for path in test_files]
        coverage_gaps = self._build_coverage_gaps(existing_tests)
        summary = self._build_summary(endpoints, existing_tests, coverage_gaps)
        risk_coverage_scores = self._build_risk_coverage_scores(coverage_gaps)
        return CoverageAnalysisResult(
            endpoint_contracts=endpoints,
            existing_tests=existing_tests,
            coverage_gaps=coverage_gaps,
            summary=summary,
            risk_coverage_scores=risk_coverage_scores,
            advisory_message=HUMAN_REVIEW_DISCLAIMER,
            approval_status=AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW,
            generated_at=datetime.now(timezone.utc),
        )

    def _discover_test_files(self, project_root: Path) -> list[Path]:
        tests_root = project_root / "tests"
        if not tests_root.exists():
            return []
        return sorted(
            path
            for path in tests_root.rglob("test_*.py")
            if "generated" not in path.parts
        )

    def _build_test_reference(
        self,
        test_path: Path,
        endpoint_paths: list[str],
    ) -> ExistingTestReference:
        content = test_path.read_text(encoding="utf-8")
        test_names = re.findall(r"def (test_[a-zA-Z0-9_]+)", content)
        matched_endpoints = [path for path in endpoint_paths if path in content]
        matched_keywords = sorted(self._extract_keywords(content))
        return ExistingTestReference(
            path=str(test_path.as_posix()),
            test_names=test_names,
            matched_endpoints=matched_endpoints,
            matched_keywords=matched_keywords,
        )

    def _build_coverage_gaps(self, tests: list[ExistingTestReference]) -> list[CoverageGap]:
        all_keywords = {keyword for test in tests for keyword in test.matched_keywords}
        all_endpoints = {endpoint for test in tests for endpoint in test.matched_endpoints}
        supporting_tests = {endpoint: [] for endpoint in all_endpoints}
        for test in tests:
            for endpoint in test.matched_endpoints:
                supporting_tests.setdefault(endpoint, []).append(test.path)

        gaps: list[CoverageGap] = []
        for item in SCENARIO_CATALOGUE:
            scenario_id = _scenario_id(item["title"])
            tags = {str(tag) for tag in item["tags"]}
            related_endpoints = [str(endpoint) for endpoint in item.get("related_endpoints", [])]
            endpoint_matches = sum(1 for endpoint in related_endpoints if endpoint in all_endpoints)
            keyword_matches = len(tags & all_keywords)
            if endpoint_matches and keyword_matches >= max(1, len(tags) // 3):
                status = CoverageStatus.COVERED
                reason = "Existing tests and keywords suggest this scenario has integration coverage."
            elif endpoint_matches or keyword_matches:
                status = CoverageStatus.PARTIAL
                reason = "Some matching tests exist, but the scenario is not fully evidenced in current test signals."
            else:
                status = CoverageStatus.MISSING
                reason = "No matching endpoint or keyword signals were found in existing integration tests."
            gaps.append(
                CoverageGap(
                    scenario_id=scenario_id,
                    title=str(item["title"]),
                    status=status,
                    risk_level=RiskLevel(item["risk_level"]),
                    reason=reason,
                    related_endpoints=related_endpoints,
                    supporting_tests=sorted(
                        {
                            test_path
                            for endpoint in related_endpoints
                            for test_path in supporting_tests.get(endpoint, [])
                        }
                    ),
                )
            )
        return gaps

    def _build_summary(
        self,
        endpoints: list[EndpointContract],
        tests: list[ExistingTestReference],
        gaps: list[CoverageGap],
    ) -> CoverageSummary:
        endpoints_with_test_signals = len({endpoint for test in tests for endpoint in test.matched_endpoints})
        high_risk_gaps = [gap for gap in gaps if gap.risk_level == RiskLevel.HIGH]
        covered_high_risk = [gap for gap in high_risk_gaps if gap.status == CoverageStatus.COVERED]
        coverage_ratio = (
            round(endpoints_with_test_signals / len(endpoints), 2)
            if endpoints
            else 0.0
        )
        high_risk_gap_ratio = (
            round(
                len([gap for gap in high_risk_gaps if gap.status != CoverageStatus.COVERED])
                / len(high_risk_gaps),
                2,
            )
            if high_risk_gaps
            else 0.0
        )
        return CoverageSummary(
            total_endpoints=len(endpoints),
            endpoints_with_test_signals=endpoints_with_test_signals,
            total_high_risk_scenarios=len(high_risk_gaps),
            covered_high_risk_scenarios=len(covered_high_risk),
            coverage_ratio=coverage_ratio,
            high_risk_gap_ratio=high_risk_gap_ratio,
        )

    def _build_risk_coverage_scores(self, gaps: list[CoverageGap]) -> list[RiskCoverageScore]:
        scenario_lookup = {
            _scenario_id(str(item["title"])): {str(tag) for tag in item["tags"]}
            for item in SCENARIO_CATALOGUE
        }
        scores: list[RiskCoverageScore] = []
        for category in RISK_COVERAGE_CATEGORIES:
            category_name = str(category["category"])
            category_tags = {str(tag) for tag in category["tags"]}
            matched_gaps = [
                gap
                for gap in gaps
                if scenario_lookup.get(gap.scenario_id, set()) & category_tags
            ]
            if not matched_gaps:
                continue
            covered = len([gap for gap in matched_gaps if gap.status == CoverageStatus.COVERED])
            partial = len([gap for gap in matched_gaps if gap.status == CoverageStatus.PARTIAL])
            missing = len([gap for gap in matched_gaps if gap.status == CoverageStatus.MISSING])
            weighted_total = covered + (partial * 0.6)
            score_percent = round((weighted_total / len(matched_gaps)) * 100)
            scores.append(
                RiskCoverageScore(
                    category=category_name,
                    score_percent=score_percent,
                    covered_scenarios=covered,
                    partial_scenarios=partial,
                    missing_scenarios=missing,
                    total_scenarios=len(matched_gaps),
                    bar=_score_bar(score_percent),
                )
            )
        return scores

    def _extract_keywords(self, content: str) -> Iterable[str]:
        lower_content = content.lower()
        keywords = {
            "query",
            "retrieval",
            "generator",
            "evidence",
            "safety",
            "refusal",
            "audit",
            "database",
            "health",
            "metrics",
            "documents",
            "prompt-injection",
            "middleware",
            "rate-limit",
            "timeout",
            "citations",
            "upload",
            "concurrency",
            "config",
            "environment",
        }
        for keyword in keywords:
            if keyword in lower_content or keyword.replace("-", "_") in lower_content:
                yield keyword


def _scenario_id(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _score_bar(score_percent: int) -> str:
    filled = min(10, max(0, round(score_percent / 10)))
    return ("█" * filled) + ("░" * (10 - filled))