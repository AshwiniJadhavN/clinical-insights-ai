"""CLI helpers for AI-assisted integration testing in CI.

This script is intentionally deterministic. It generates advisory-only outputs
that require human review and must not gate deployments on their own.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import app  # noqa: E402
from backend.testing_ai.models import FailureAnalysisRequest  # noqa: E402
from backend.testing_ai.services import TestingAIService  # noqa: E402


def _service(project_root: Path) -> TestingAIService:
    return TestingAIService(
        project_root=project_root,
        audit_trail_directory=project_root / "backend/audit/trail",
        generated_tests_directory=project_root / "tests/generated",
        report_directory=project_root / "docs/testing",
    )


def generate_report(project_root: Path) -> int:
    result = _service(project_root).generate_report(app.routes)
    print(result.report_path)
    return 0


def analyze_failure(project_root: Path, pytest_path: Path, github_actions_path: Path | None, application_log_path: Path | None) -> int:
    request = FailureAnalysisRequest(
        pytest_output=pytest_path.read_text(encoding="utf-8"),
        github_actions_log=github_actions_path.read_text(encoding="utf-8") if github_actions_path and github_actions_path.exists() else "",
        application_log=application_log_path.read_text(encoding="utf-8") if application_log_path and application_log_path.exists() else "",
    )
    result = _service(project_root).analyze_failure(request)
    output_path = project_root / "artifacts/testing-ai/failure-analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
    print(output_path.as_posix())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-assisted integration testing CI helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("generate-report")
    report_parser.add_argument("--project-root", default=".")

    failure_parser = subparsers.add_parser("analyze-failure")
    failure_parser.add_argument("--project-root", default=".")
    failure_parser.add_argument("--pytest-output", required=True)
    failure_parser.add_argument("--github-actions-log")
    failure_parser.add_argument("--application-log")

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    if args.command == "generate-report":
        return generate_report(project_root)
    return analyze_failure(
        project_root,
        Path(args.pytest_output),
        Path(args.github_actions_log) if args.github_actions_log else None,
        Path(args.application_log) if args.application_log else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())