"""
RAG evaluation metrics.

All functions are pure — no side effects, no external calls, no models.
All metrics return float in [0.0, 1.0]. Empty-input edge cases return 0.0.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_OVERLAP: int = 3


@dataclass(frozen=True)
class RetrievalMetrics:
    precision: float
    recall: float
    f1: float
    mrr: float


def retrieval_precision(retrieved: list[str], relevant: set[str]) -> float:
    if not retrieved:
        return 0.0
    return sum(1 for r in retrieved if r in relevant) / len(retrieved)


def retrieval_recall(retrieved: list[str], relevant: set[str]) -> float:
    if not relevant:
        return 0.0
    return sum(1 for r in relevant if r in retrieved) / len(relevant)


def f1_score(precision: float, recall: float) -> float:
    denom = precision + recall
    return 0.0 if denom == 0.0 else 2 * precision * recall / denom


def mean_reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def answer_coverage(answer: str, chunks: list[str], min_overlap: int = DEFAULT_OVERLAP) -> float:
    if not chunks or not answer:
        return 0.0
    answer_lower = answer.lower()
    covered = 0
    for chunk in chunks:
        words = chunk.lower().split()
        if len(words) < min_overlap:
            if chunk.lower().strip() in answer_lower:
                covered += 1
            continue
        if any(" ".join(words[i: i + min_overlap]) in answer_lower
               for i in range(len(words) - min_overlap + 1)):
            covered += 1
    return covered / len(chunks)


def compute_retrieval_metrics(retrieved: list[str], relevant: set[str]) -> RetrievalMetrics:
    p = retrieval_precision(retrieved, relevant)
    r = retrieval_recall(retrieved, relevant)
    return RetrievalMetrics(
        precision=round(p, 4), recall=round(r, 4),
        f1=round(f1_score(p, r), 4),
        mrr=round(mean_reciprocal_rank(retrieved, relevant), 4),
    )
