"""Service orchestration for AI-assisted integration testing."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from fastapi.routing import APIRoute

from backend.testing_ai.coverage_analyzer import CoverageAnalyzer
from backend.testing_ai.failure_analyzer import FailureAnalyzer
from backend.testing_ai.models import (
    EndpointContract,
    FailureAnalysisRequest,
    FailureAnalysisResponse,
    GenerateTestsRequest,
    GenerateTestsResponse,
    ReportResponse,
    RiskMapRequest,
    RiskMapResponse,
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
)
from backend.testing_ai.prompt_templates import HUMAN_REVIEW_DISCLAIMER
from backend.testing_ai.report_generator import ReportGenerator
from backend.testing_ai.risk_mapper import RiskMapper
from backend.testing_ai.scenario_generator import ScenarioGenerator
from backend.testing_ai.test_generator import TestGenerator


class TestingAIService:
    """Coordinate deterministic, human-reviewed testing analysis outputs."""

    __test__ = False

    def __init__(
        self,
        project_root: Path,
        audit_trail_directory: Path,
        generated_tests_directory: Path,
        report_directory: Path,
    ) -> None:
        self._project_root = project_root
        self._audit_trail_directory = audit_trail_directory
        self._generated_tests_directory = generated_tests_directory
        self._report_directory = report_directory
        self._coverage_analyzer = CoverageAnalyzer()
        self._scenario_generator = ScenarioGenerator()
        self._test_generator = TestGenerator()
        self._risk_mapper = RiskMapper()
        self._failure_analyzer = FailureAnalyzer()
        self._report_generator = ReportGenerator()

    def generate_scenarios(
        self,
        request: ScenarioGenerationRequest,
        app_routes: Sequence[object],
    ) -> ScenarioGenerationResponse:
        endpoint_contracts = self._collect_endpoint_contracts(app_routes)
        coverage = self._coverage_analyzer.analyze(self._project_root, endpoint_contracts)
        audit_evidence = self._load_audit_evidence()
        if request.audit_log_excerpt.strip():
            audit_evidence.insert(
                0,
                self._build_inline_audit_evidence(request.audit_log_excerpt),
            )
        scenarios = self._scenario_generator.generate(
            coverage=coverage,
            audit_evidence=audit_evidence,
            manual_requirements=request.manual_requirements,
            target_endpoints=request.target_endpoints,
            max_scenarios=request.max_scenarios,
        )
        return ScenarioGenerationResponse(
            scenarios=scenarios,
            coverage=coverage,
            human_review_required=True,
            advisory_message=HUMAN_REVIEW_DISCLAIMER,
            generated_at=datetime.now(timezone.utc),
        )

    def generate_tests(
        self,
        request: GenerateTestsRequest,
        app_routes: Sequence[object],
    ) -> GenerateTestsResponse:
        scenarios = request.scenarios
        if not scenarios:
            scenario_response = self.generate_scenarios(
                ScenarioGenerationRequest(),
                app_routes,
            )
            scenarios = scenario_response.scenarios[:5]
        output_directory = self._project_root / request.output_directory
        generated_files = self._test_generator.generate(
            scenarios=scenarios,
            output_directory=output_directory,
            file_prefix=request.file_prefix,
        )
        return GenerateTestsResponse(
            generated_files=generated_files,
            human_review_required=True,
            advisory_message=HUMAN_REVIEW_DISCLAIMER,
            generated_at=datetime.now(timezone.utc),
        )

    def map_risk(
        self,
        request: RiskMapRequest,
    ) -> RiskMapResponse:
        mappings = self._risk_mapper.map(request.requirements, request.scenarios)
        return RiskMapResponse(
            mappings=mappings,
            human_review_required=True,
            advisory_message=HUMAN_REVIEW_DISCLAIMER,
            generated_at=datetime.now(timezone.utc),
        )

    def analyze_failure(
        self,
        request: FailureAnalysisRequest,
    ) -> FailureAnalysisResponse:
        return self._failure_analyzer.analyze(
            pytest_output=request.pytest_output,
            github_actions_log=request.github_actions_log,
            application_log=request.application_log,
        )

    def generate_report(self, app_routes: Sequence[object]) -> ReportResponse:
        endpoint_contracts = self._collect_endpoint_contracts(app_routes)
        coverage = self._coverage_analyzer.analyze(self._project_root, endpoint_contracts)
        generated_tests = self._discover_generated_tests()
        report_path, graph_path, markdown, integration_graph, recommendations = self._report_generator.generate(
            report_directory=self._report_directory,
            coverage=coverage,
            generated_tests=generated_tests,
        )
        return ReportResponse(
            report_path=str(report_path.as_posix()),
            graph_path=str(graph_path.as_posix()),
            markdown=markdown,
            integration_test_graph=integration_graph,
            coverage=coverage,
            generated_tests=generated_tests,
            recommendations=recommendations,
            human_review_required=True,
            advisory_message=HUMAN_REVIEW_DISCLAIMER,
            generated_at=datetime.now(timezone.utc),
        )

    def _collect_endpoint_contracts(self, app_routes: Sequence[object]) -> list[EndpointContract]:
        contracts: list[EndpointContract] = []
        for route in app_routes:
            if not isinstance(route, APIRoute):
                continue
            if route.path.startswith(("/docs", "/redoc", "/openapi.json")):
                continue
            contracts.append(
                EndpointContract(
                    path=route.path,
                    methods=sorted(method for method in (route.methods or set()) if method != "HEAD"),
                    summary=route.summary or "",
                    response_model=(
                        getattr(route.response_model, "__name__", str(route.response_model))
                        if route.response_model
                        else None
                    ),
                    tags=[str(tag) for tag in (route.tags or [])],
                )
            )
        return sorted(contracts, key=lambda item: item.path)

    def _load_audit_evidence(self):
        from backend.testing_ai.models import EvidenceItem, EvidenceSourceType

        evidence: list[EvidenceItem] = []
        if not self._audit_trail_directory.exists():
            return evidence
        for path in sorted(self._audit_trail_directory.glob("*.jsonl")):
            lines = path.read_text(encoding="utf-8").splitlines()
            for line_number, line in enumerate(lines[-3:], start=max(1, len(lines) - 2)):
                evidence.append(
                    EvidenceItem(
                        source_type=EvidenceSourceType.AUDIT_LOG,
                        source_name=str(path.as_posix()),
                        excerpt=line[:500],
                        line_number=line_number,
                    )
                )
        return evidence[:4]

    def _build_inline_audit_evidence(self, audit_log_excerpt: str):
        from backend.testing_ai.models import EvidenceItem, EvidenceSourceType

        first_line = audit_log_excerpt.splitlines()[0][:500]
        return EvidenceItem(
            source_type=EvidenceSourceType.AUDIT_LOG,
            source_name="inline_audit_excerpt",
            excerpt=first_line or "Inline audit excerpt provided.",
            line_number=1,
        )

    def _discover_generated_tests(self):
        from backend.testing_ai.models import GeneratedTestFile

        generated_files = []
        if not self._generated_tests_directory.exists():
            return generated_files
        for path in sorted(self._generated_tests_directory.glob("*_template.py")):
            title = path.stem.replace("_template", "").replace("_", " ").title()
            generated_files.append(
                GeneratedTestFile(
                    path=str(path.as_posix()),
                    scenario_id=path.stem,
                    title=title,
                    human_review_required=True,
                    advisory_message=HUMAN_REVIEW_DISCLAIMER,
                )
            )
        return generated_files