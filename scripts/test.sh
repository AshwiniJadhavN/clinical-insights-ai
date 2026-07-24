#!/usr/bin/env bash
set -euo pipefail

ruff check .
pytest --cov=backend --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml --cov-fail-under=70
python scripts/critical_coverage_check.py coverage.xml
