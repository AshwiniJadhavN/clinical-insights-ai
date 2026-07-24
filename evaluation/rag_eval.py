"""Deterministic retrieval evaluation for CI."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RetrievalEvalCase:
    question: str
    expected_source: str
    required_terms: list[str]


@dataclass(frozen=True)
class RetrievalEvalResult:
    passed: bool
    accuracy: float
    min_accuracy: float
    failures: list[str]


def run_retrieval_eval(dataset_path: Path, docs_dir: Path) -> RetrievalEvalResult:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = [
        RetrievalEvalCase(
            question=str(case["question"]),
            expected_source=str(case["expected_source"]),
            required_terms=[str(term) for term in case.get("required_terms", [])],
        )
        for case in dataset.get("cases", [])
    ]
    min_accuracy = float(dataset.get("min_accuracy", 1.0))
    corpus = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(docs_dir.glob("*.txt"))
    }

    failures: list[str] = []
    hits = 0
    for case in cases:
        ranked = rank_documents(case.question, corpus)
        top_source = ranked[0][0] if ranked else None
        expected_text = corpus.get(case.expected_source, "")
        required_terms_present = all(
            term.lower() in expected_text.lower() for term in case.required_terms
        )
        if top_source == case.expected_source and required_terms_present:
            hits += 1
            continue
        failures.append(
            f"{case.question} expected={case.expected_source} actual={top_source}"
        )

    accuracy = hits / len(cases) if cases else 0.0
    return RetrievalEvalResult(
        passed=accuracy >= min_accuracy,
        accuracy=round(accuracy, 4),
        min_accuracy=min_accuracy,
        failures=failures,
    )


def rank_documents(question: str, corpus: dict[str, str]) -> list[tuple[str, float]]:
    query_terms = _tokens(question)
    scored = [
        (name, _score(query_terms, _tokens(text)))
        for name, text in corpus.items()
    ]
    return sorted(scored, key=lambda item: item[1], reverse=True)


def result_to_json(result: RetrievalEvalResult) -> dict[str, Any]:
    return {
        "passed": result.passed,
        "accuracy": result.accuracy,
        "min_accuracy": result.min_accuracy,
        "failures": result.failures,
    }


def _score(query_terms: set[str], document_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    overlap = query_terms.intersection(document_terms)
    return len(overlap) / len(query_terms)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9.]+", value.lower())
        if len(token) > 2
    }
