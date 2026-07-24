"""FastAPI routes for AI-assisted integration testing."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request

from backend.config import Settings, get_settings
from backend.testing_ai.models import (
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
from backend.testing_ai.services import TestingAIService

router = APIRouter()


def get_testing_ai_service(settings: Settings = Depends(get_settings)) -> TestingAIService:
    project_root = Path(".").resolve()
    return TestingAIService(
        project_root=project_root,
        audit_trail_directory=project_root / settings.audit_trail_directory,
        generated_tests_directory=project_root / "tests/generated",
        report_directory=project_root / "docs/testing",
    )


@router.post(
    "/generate-scenarios",
    response_model=ScenarioGenerationResponse,
    summary="Generate draft integration scenarios",
    description=(
        "Analyze endpoint contracts, existing tests, and optional audit logs to "
        "propose advisory integration scenarios that require human review."
    ),
)
def generate_scenarios(
    body: ScenarioGenerationRequest,
    request: Request,
    service: TestingAIService = Depends(get_testing_ai_service),
) -> ScenarioGenerationResponse:
    return service.generate_scenarios(body, request.app.routes)


@router.post(
    "/generate-tests",
    response_model=GenerateTestsResponse,
    summary="Generate draft pytest integration templates",
    description=(
        "Create non-destructive pytest draft files under tests/generated. Files are "
        "advisory only and must be reviewed before any execution or approval."
    ),
)
def generate_tests(
    body: GenerateTestsRequest,
    request: Request,
    service: TestingAIService = Depends(get_testing_ai_service),
) -> GenerateTestsResponse:
    return service.generate_tests(body, request.app.routes)


@router.post(
    "/analyze-failure",
    response_model=FailureAnalysisResponse,
    summary="Analyze pytest and CI failures",
    description="Return structured JSON describing likely root cause and next debugging steps.",
)
def analyze_failure(
    body: FailureAnalysisRequest,
    service: TestingAIService = Depends(get_testing_ai_service),
) -> FailureAnalysisResponse:
    return service.analyze_failure(body)


@router.post(
    "/map-risk",
    response_model=RiskMapResponse,
    summary="Map requirements to risks and draft tests",
    description=(
        "Return a requirement -> behavior -> risk -> test -> expected result -> "
        "evidence mapping as structured JSON."
    ),
)
def map_risk(
    body: RiskMapRequest,
    service: TestingAIService = Depends(get_testing_ai_service),
) -> RiskMapResponse:
    return service.map_risk(body)


@router.get(
    "/report",
    response_model=ReportResponse,
    summary="Generate an advisory integration testing report",
    description="Write a markdown report under docs/testing and return the generated content.",
)
def get_report(
    request: Request,
    service: TestingAIService = Depends(get_testing_ai_service),
) -> ReportResponse:
    return service.generate_report(request.app.routes)