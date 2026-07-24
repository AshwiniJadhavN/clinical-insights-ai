"""Strict models for AI-assisted integration testing outputs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdvisoryApprovalStatus(str, Enum):
    DRAFT_NEEDS_HUMAN_REVIEW = "draft_needs_human_review"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    MISSING = "missing"


class EvidenceSourceType(str, Enum):
    ENDPOINT = "endpoint"
    TEST_FILE = "test_file"
    AUDIT_LOG = "audit_log"
    CI_LOG = "ci_log"
    APPLICATION_LOG = "application_log"
    GENERATED_TEMPLATE = "generated_template"
    REPORT = "report"


class EndpointContract(BaseModel):
    path: str = Field(min_length=1)
    methods: list[str] = Field(min_length=1)
    summary: str = ""
    response_model: str | None = None
    tags: list[str] = []


class ExistingTestReference(BaseModel):
    path: str = Field(min_length=1)
    test_names: list[str] = []
    matched_endpoints: list[str] = []
    matched_keywords: list[str] = []


class EvidenceItem(BaseModel):
    source_type: EvidenceSourceType
    source_name: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    line_number: int | None = Field(default=None, ge=1)


class ScenarioDraft(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    requirement: str = Field(min_length=1)
    system_behavior: str = Field(min_length=1)
    risk: str = Field(min_length=1)
    risk_level: RiskLevel
    expected_result: str = Field(min_length=1)
    evidence_to_collect: list[str] = Field(min_length=1)
    related_endpoints: list[str] = []
    rationale: str = Field(min_length=1)
    based_on: list[EvidenceItem] = Field(min_length=1)
    human_review_required: bool = True
    advisory_message: str = Field(min_length=1)


class CoverageGap(BaseModel):
    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: CoverageStatus
    risk_level: RiskLevel
    reason: str = Field(min_length=1)
    related_endpoints: list[str] = []
    supporting_tests: list[str] = []


class CoverageSummary(BaseModel):
    total_endpoints: int = Field(ge=0)
    endpoints_with_test_signals: int = Field(ge=0)
    total_high_risk_scenarios: int = Field(ge=0)
    covered_high_risk_scenarios: int = Field(ge=0)
    coverage_ratio: float = Field(ge=0.0, le=1.0)
    high_risk_gap_ratio: float = Field(ge=0.0, le=1.0)


class RiskCoverageScore(BaseModel):
    category: str = Field(min_length=1)
    score_percent: int = Field(ge=0, le=100)
    covered_scenarios: int = Field(ge=0)
    partial_scenarios: int = Field(ge=0)
    missing_scenarios: int = Field(ge=0)
    total_scenarios: int = Field(ge=0)
    bar: str = Field(min_length=1)


class CoverageAnalysisResult(BaseModel):
    endpoint_contracts: list[EndpointContract]
    existing_tests: list[ExistingTestReference]
    coverage_gaps: list[CoverageGap]
    summary: CoverageSummary
    risk_coverage_scores: list[RiskCoverageScore]
    advisory_message: str
    approval_status: AdvisoryApprovalStatus = AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW
    generated_at: datetime


class ScenarioGenerationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    manual_requirements: list[str] = []
    audit_log_excerpt: str = ""
    max_scenarios: int = Field(default=10, ge=1, le=25)
    target_endpoints: list[str] = []


class ScenarioGenerationResponse(BaseModel):
    scenarios: list[ScenarioDraft]
    coverage: CoverageAnalysisResult
    human_review_required: bool = True
    approval_status: AdvisoryApprovalStatus = AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW
    advisory_message: str
    generated_at: datetime


class GenerateTestsRequest(BaseModel):
    scenarios: list[ScenarioDraft] = []
    output_directory: str = "tests/generated"
    file_prefix: str = "draft"
    overwrite_existing: bool = False

    @field_validator("overwrite_existing")
    @classmethod
    def forbid_overwrite(cls, value: bool) -> bool:
        if value:
            raise ValueError("Generated tests must never overwrite existing files.")
        return value


class GeneratedTestFile(BaseModel):
    path: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    human_review_required: bool = True
    advisory_message: str = Field(min_length=1)


class GenerateTestsResponse(BaseModel):
    generated_files: list[GeneratedTestFile]
    human_review_required: bool = True
    approval_status: AdvisoryApprovalStatus = AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW
    advisory_message: str
    generated_at: datetime


class RiskMapRequest(BaseModel):
    requirements: list[str] = []
    scenarios: list[ScenarioDraft] = []


class RiskMapEntry(BaseModel):
    requirement: str = Field(min_length=1)
    system_behavior: str = Field(min_length=1)
    risk: str = Field(min_length=1)
    integration_test: str = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    evidence_collected: list[str] = Field(min_length=1)
    risk_level: RiskLevel
    related_endpoints: list[str] = []
    human_review_required: bool = True


class RiskMapResponse(BaseModel):
    mappings: list[RiskMapEntry]
    human_review_required: bool = True
    approval_status: AdvisoryApprovalStatus = AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW
    advisory_message: str
    generated_at: datetime


class FailureAnalysisRequest(BaseModel):
    pytest_output: str = Field(min_length=1)
    github_actions_log: str = ""
    application_log: str = ""


class FailureAnalysisResponse(BaseModel):
    root_cause_summary: str = Field(min_length=1)
    likely_failing_component: str = Field(min_length=1)
    confidence_score: float = Field(ge=0.0, le=1.0)
    suggested_next_debugging_steps: list[str] = Field(min_length=1)
    possible_fix: str = Field(min_length=1)
    supporting_evidence: list[EvidenceItem] = Field(min_length=1)
    human_review_required: bool = True
    approval_status: AdvisoryApprovalStatus = AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW
    advisory_message: str
    generated_at: datetime


class ReportResponse(BaseModel):
    report_path: str = Field(min_length=1)
    graph_path: str = Field(min_length=1)
    markdown: str = Field(min_length=1)
    integration_test_graph: str = Field(min_length=1)
    coverage: CoverageAnalysisResult
    generated_tests: list[GeneratedTestFile]
    recommendations: list[str]
    human_review_required: bool = True
    approval_status: AdvisoryApprovalStatus = AdvisoryApprovalStatus.DRAFT_NEEDS_HUMAN_REVIEW
    advisory_message: str
    generated_at: datetime