# Clinical Insights AI

Clinical document Q&A with source citations, evidence checks, and explicit refusal behaviour.

A reference implementation showing how retrieval, generation, safety decisions, and audit metadata fit into an inspectable software workflow.

**Synthetic data only. Not intended for clinical use. Do not upload real patient data.** See [DISCLAIMER.md](DISCLAIMER.md).

## The Problem

Clinical and operational documents can be long and difficult to search. A document assistant should help users inspect the evidence behind an answer and recognise when the available information is insufficient.

This project explores that workflow: retrieve relevant passages, check the evidence, and generate an answer with citations or return an explicit refusal or clarification response.

## See It in Action

- Watch the demo: [docs/demo/demo.mp4](docs/demo/demo.mp4)
- Five-minute reviewer guide: [docs/reviewer_guide.md](docs/reviewer_guide.md)

## What It Does

- **Ingests documents**: accepts PDF and text files, chunks their content, and indexes it for retrieval.
- **Checks evidence before generation**: applies retrieval thresholds and safety policies.
- **Makes sources inspectable**: returns document references, excerpts, and citation metadata.
- **Handles unsupported requests**: includes responses for insufficient evidence, conflicts, policy violations, and generation timeouts.
- **Supports review**: records query metadata and connects structured safety findings to requirements, hazards, and controls.

Built with FastAPI, with separate services for document handling, query orchestration, safety decisions, and auditing. Local development supports SQLite; Docker Compose provides a PostgreSQL-backed path. Both supplied startup paths default to mock language-model mode.

## Why This Design

The central design choice is to make evidence checks and response decisions explicit.

1. **Prepare the evidence**: ingest documents, split them into chunks, and index them. → [Document service](backend/services/document_service.py)
2. **Retrieve relevant passages**: embed the question and search indexed content. → [Query service](backend/services/query_service.py)
3. **Check the evidence**: apply retrieval thresholds and safety rules before generation. → [Refusal logic](backend/refusal/logic.py)
4. **Choose a response**: proceed with generation, request clarification, or decline to answer. → [Decision engine](backend/safety/decision_engine.py)
5. **Check generated output**: verify citation identifiers and excerpts, then apply output rules. → [Safety orchestration](backend/safety/decision_engine.py)
6. **Record review metadata**: capture identifiers, decisions, versions, and timing. → [Audit service](backend/services/audit_service.py)

The [query service](backend/services/query_service.py) receives retrieval, generation, and safety dependencies through its constructor, keeping orchestration separate from their implementations.

Citation checks establish whether references match retrieved sources. They do not establish that every generated claim is correct.

## My Contribution

My focus is connecting the document-review workflow with concrete engineering decisions: API design, query orchestration, data validation, evidence checks, refusal behaviour, and traceability.

The code, evaluations, and architecture notes show how those decisions are implemented, tested, and bounded by explicit assumptions.

## Engineering Highlights

| Design Choice | Purpose | Code |
|---|---|---|
| Injected retrieval and generation dependencies | Separate orchestration from adapters and support controlled tests | [Query service](backend/services/query_service.py) |
| Evidence checks before generation | Stop generation when retrieval fails configured thresholds | [Refusal logic](backend/refusal/logic.py) |
| Structured safety decisions | Make refusal, clarification, and review requirements explicit | [Decision engine](backend/safety/decision_engine.py) |
| Citation verification | Check source identifiers and excerpts against retrieved chunks | [Citation verifier](backend/safety/citation_verifier.py) |
| Query audit metadata | Record identifiers, decisions, versions, and timing without storing raw question or answer text in the query audit service | [Audit service](backend/services/audit_service.py) |

See also: [Engineering tradeoffs](docs/engineering_tradeoffs.md) · [Architecture decisions](docs/adr/README.md)

## Evaluation Evidence

Recorded deterministic local baseline: 10 July 2026.

| Evaluation | Recorded Result | Evidence |
|---|---|---|
| Top-1 retrieval accuracy | 8/8 cases | [Retrieval harness](evals/retrieval_eval.py) |
| Top-3 retrieval accuracy | 8/8 cases | [Retrieval harness](evals/retrieval_eval.py) |
| Refusal and adversarial cases | 9/9 passed | [Refusal harness](evals/refusal_eval.py) |

These small regression suites check predefined behaviours using synthetic data. The retrieval harness uses a deterministic token embedder; these results do not establish runtime model performance or clinical effectiveness.

Reproduce locally:

```bash
make eval
```

See: [Evaluation methods and limitations](docs/evaluation.md)

## Quick Start

Use Python 3.11 or later.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
scripts/run_local.sh
```

Open `http://localhost:8000/docs`. The local script defaults to mock language-model mode for development.

**Or Docker Compose:**

```bash
cp .env.example .env
scripts/deploy_local.sh
curl http://localhost:8000/health
```

## Quality Checks

```bash
make lint        # Ruff
make test        # Enforces a 78% coverage threshold
make eval        # Deterministic benchmarks
make smoke-test  # Health endpoint checks
make load-test   # k6 load test
```

The [continuous integration workflow](.github/workflows/ci.yml) defines lint, type checks, tests, coverage, security scans, evaluation, build, and smoke-test checks.

Coverage thresholds currently differ: `make test` specifies 78%, while the continuous integration coverage job specifies 70% with [explicit coverage configuration](.coveragerc). These are configured thresholds, not reported coverage results.

The smoke test checks `/health/live` and `/health`. A separate `make load-test` target runs the k6 load-test script and requires k6 installed and the application running.

See [latest workflow runs](https://github.com/AshwiniJadhavN/clinical-insights-ai/actions) for execution results.

## What This Demonstrates

- **System design**: API boundaries, retrieval orchestration, safety decisions, and audit metadata.
- **Evidence-first workflow**: document ingestion, retrieval checks, explicit response decisions, and source inspection.
- **MedTech engineering judgment**: traceability, refusal behaviour, repeatable evaluation, and clear intended-use boundaries.
- **Delivery practices**: containerized local setup, automated quality checks, architecture documentation, and runbooks.

## Scope and Current Limits

This is an engineering reference, not a clinical product. It does not claim clinical validation, HIPAA compliance, FDA clearance, or readiness for clinical deployment.

Retrieval confidence and output checks are heuristic. Query audit coverage is incomplete: early input refusals bypass the audit call, and audit write failures are logged without failing the query.

The separate JSONL audit writer supports hash-chain integrity checks; it does not provide immutable storage.

See [full scope and data-handling boundaries](DISCLAIMER.md).

## Further Reading

**For reviewers:**

- [Five-minute reviewer guide](docs/reviewer_guide.md)
- [Architecture overview](docs/architecture.md)
- [Detailed architecture views](docs/architecture/README.md)

**For deeper dives:**

- [Engineering tradeoffs](docs/engineering_tradeoffs.md)
- [Evaluation methods and limitations](docs/evaluation.md)
- [Observability playbook](docs/runbooks/observability_playbook_lite.md)
- [Architecture decision records](docs/adr/README.md)
