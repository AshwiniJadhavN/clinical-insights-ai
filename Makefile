PYTHON ?= $(shell if [ -x .venv311/bin/python ]; then echo .venv311/bin/python; elif [ -x .venv/bin/python ]; then echo .venv/bin/python; else command -v python3; fi)

.PHONY: lint test smoke-test benchmark benchmark-save load-test eval-retrieval eval-refusal eval build deploy-local run-local ci-local install-hooks

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest --cov=backend --cov-report=term-missing --cov-report=xml --cov-fail-under=78

smoke-test:
	PYTHON="$(PYTHON)" bash scripts/smoke_test.sh

benchmark:
	$(PYTHON) scripts/benchmark_api.py --url http://localhost:8000/health --requests 100 --warmup 10

benchmark-save:
	$(PYTHON) scripts/benchmark_api.py --url http://localhost:8000/health --requests 100 --warmup 10 --save-json

load-test:
	k6 run tests/load/k6_smoke.js

eval-retrieval:
	$(PYTHON) evals/retrieval_eval.py

eval-refusal:
	$(PYTHON) evals/refusal_eval.py

eval: eval-retrieval eval-refusal

install-hooks:
	$(PYTHON) -m pip install pre-commit --quiet
	pre-commit install
	@echo "Pre-commit hooks installed. They will run automatically on git commit."

build:
	scripts/build_image.sh

deploy-local:
	scripts/deploy_local.sh

run-local:
	scripts/run_local.sh

ci-local: lint test smoke-test
