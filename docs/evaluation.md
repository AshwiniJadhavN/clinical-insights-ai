# Evaluation

This repository includes two deterministic local evaluation harnesses:

1. Retrieval evaluation against representative questions and expected evidence sources in `evals/test_queries.json`.
2. Refusal and adversarial evaluation against the query safety path using explicit local mocks for retrieval and generation.

## What Was Tested

### Retrieval evaluation

The retrieval evaluation checks whether representative demonstration questions retrieve the expected source document from `data/sample_docs/`.

The current dataset includes both straightforward evidence lookups and harder wording variations that still map back to the same source document identifiers.

It measures:

- Top-1 retrieval accuracy: whether the expected source is the first returned result.
- Top-3 retrieval accuracy: whether the expected source appears anywhere in the first three returned results.
- Missing evidence cases: questions where no expected source appears in the first three results.
- Average retrieval latency: average time spent ranking the local sample corpus per query.

The retrieval harness is deterministic and local. It uses a simple lexical ranking function over the sample corpus so results are reproducible without downloading models or calling external services.
The current implementation is closer to the runtime retrieval path than a plain lexical check: it uses the project's chunking logic, builds deterministic local token-vector embeddings, and ranks chunk similarity offline without any external model or vector database dependency.

### Refusal and adversarial evaluation

The refusal evaluation exercises the existing `QueryService` and `SafetyDecisionEngine` with explicit local mocks for retrieval and generation.

It covers:

- no evidence available
- weak evidence
- conflicting evidence
- request for diagnosis
- request for treatment advice
- question outside document scope
- prompt-injection attempt

It also includes extra failure-oriented scenarios such as high-risk oncology evidence that misses the stricter threshold and treatment advice generated from limited trial evidence.

For each case, the harness checks whether the system safely refuses, asks for clarification, or returns insufficient-evidence behavior, and records the decision reason.

## How To Run

From the repository root:

```bash
make eval-retrieval
make eval-refusal
make eval
```

Direct script entry points are also available:

```bash
python3 evals/retrieval_eval.py
python3 evals/refusal_eval.py
```

The Make targets prefer the repository virtual environment when `.venv311/` or `.venv/` is present, which keeps local results reproducible even when the shell is not activated into the environment.

## Metric Meaning

- Top-1 retrieval accuracy is a precision-style check for the first returned result only.
- Top-3 retrieval accuracy is a looser recall-style check for whether the expected evidence is surfaced near the top of the ranking.
- Missing evidence cases highlight questions where the expected evidence was not surfaced at all in the inspected window.
- Average retrieval latency is only a local benchmark for the deterministic evaluation harness. It is not a production performance claim.
- Refusal pass/fail indicates whether the observed safety decision matched the expected behavior for the scenario and included the expected reason fragment.

## Current Limitations

- The retrieval harness uses deterministic lexical matching over the sample corpus rather than the production vector stack.
- The refusal harness uses explicit mocks for retrieval and generation so it can test safety behavior locally and reproducibly.
- The retrieval harness is still an offline approximation of production retrieval even though it exercises chunking and chunk-level similarity ranking.
- The datasets are small and demonstration-oriented; they do not measure broad real-world retrieval coverage or failure distributions.
- These evals do not validate clinical correctness.
- These evals do not demonstrate HIPAA compliance, medical safety, or deployment readiness.

## Scope and Non-Claims

These evaluations are engineering evidence, not clinical validation.

They demonstrate engineering controls around:

- evidence grounding expectations
- refusal and clarification behavior
- deterministic local verification
- safety-path observability during evaluation

They do not establish medical accuracy, regulatory approval, or suitability for clinical use.

## CI Gates

GitHub Actions now runs separate evaluation gates for retrieval behavior and refusal/adversarial behavior. Those gates are defined in `.github/workflows/ci.yml` and feed into the final CI summary alongside the repository's other engineering checks.