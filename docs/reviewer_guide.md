# Reviewer Guide (5-Minute Path)

This guide is for architecture, safety, and quality walkthroughs. It focuses on engineering signals and explicit non-claims.

> This repository demonstrates engineering controls around RAG grounding, refusal behavior, auditability, and operational checks. It is not clinical validation.

## 1) Project Purpose (about 30 seconds)

- Purpose statement: [README.md](../README.md)
- Scope and non-claims: [README.md](../README.md#limitations-and-non-claims)

What to look for:
- The project intentionally demonstrates safe RAG behavior and reviewability.
- The repository avoids claims of clinical validity or medical-device readiness.

## 2) Architecture (about 1 minute)

- Architecture overview: [docs/architecture.md](architecture.md)
- Detailed architecture index: [docs/architecture/README.md](architecture/README.md)
- Runtime bootstrap boundary: [backend/main.py](../backend/main.py)

What to look for:
- Separation between API routes, orchestration services, RAG adapters, refusal/safety, and audit.
- Explicit boundaries for retrieval, generation, and policy decisions.

## 3) Safety and Refusal Logic (about 1 minute)

- Retrieval refusal thresholds: [backend/refusal/logic.py](../backend/refusal/logic.py)
- Safety decision orchestration: [backend/safety/decision_engine.py](../backend/safety/decision_engine.py)
- Policy enforcement rules: [backend/safety/policy.py](../backend/safety/policy.py)
- Query pipeline decision points: [backend/services/query_service.py](../backend/services/query_service.py)

What to look for:
- Weak or missing evidence blocks answer generation.
- Prompt-injection and unsafe output paths are explicitly handled.
- Decision outputs are structured and auditable.

## 4) Evaluation Evidence (about 1 minute)

- Evaluation overview and limitations: [docs/evaluation.md](evaluation.md)
- Retrieval harness: [evals/retrieval_eval.py](../evals/retrieval_eval.py)
- Refusal/adversarial harness: [evals/refusal_eval.py](../evals/refusal_eval.py)
- Retrieval dataset: [evals/test_queries.json](../evals/test_queries.json)

What to look for:
- Deterministic local evaluation with reproducible commands.
- Explicit engineering scope rather than clinical-performance claims.

## 5) CI/CD and Quality Gates (about 45 seconds)

- CI workflow: [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- Container workflow: [.github/workflows/cd.yml](../.github/workflows/cd.yml)

What to look for:
- Lint, tests, coverage, safety-oriented canaries, retrieval/refusal eval gates, and integration checks.
- Artifact-based gate reporting for review traceability.

## 6) Run Locally (about 45 seconds)

- Local run script: [scripts/run_local.sh](../scripts/run_local.sh)
- Docker local runtime: [scripts/deploy_local.sh](../scripts/deploy_local.sh)
- Make targets: [Makefile](../Makefile)

Suggested quick commands:

```bash
make eval
make test
scripts/run_local.sh
```

Optional performance command:

```bash
python3 scripts/benchmark_api.py --url http://localhost:8000/health --requests 100 --warmup 10 --save-json
```

Generated benchmark JSON files are written to `docs/performance/`.
