"""Prometheus metrics for RAG and advisory automation controls."""

from __future__ import annotations

from prometheus_client import Counter, Gauge

RAG_RETRIEVAL_ATTEMPTS = Counter(
    "rag_retrieval_attempts_total",
    "Total RAG retrieval attempts.",
)
RAG_RETRIEVAL_HITS = Counter(
    "rag_retrieval_hits_total",
    "RAG retrieval attempts with at least one chunk above the confidence threshold.",
)
RAG_RETRIEVAL_HIT_RATE = Gauge(
    "rag_retrieval_hit_rate",
    "Ratio of successful RAG retrieval hits to retrieval attempts.",
)
ADVISORY_REFUSALS_TOTAL = Counter(
    "advisory_refusals_total",
    "Total advisory draft requests refused by governance or safety controls.",
    ["reason"],
)
ADVISORY_APPROVED_TOTAL = Counter(
    "advisory_approved_total",
    "Total advisory drafts marked as approved after human review.",
)

_retrieval_attempts = 0
_retrieval_hits = 0


def record_rag_retrieval(hit: bool) -> None:
    global _retrieval_attempts, _retrieval_hits
    _retrieval_attempts += 1
    RAG_RETRIEVAL_ATTEMPTS.inc()
    if hit:
        _retrieval_hits += 1
        RAG_RETRIEVAL_HITS.inc()
    RAG_RETRIEVAL_HIT_RATE.set(_retrieval_hits / _retrieval_attempts)


def record_advisory_refusal(reason: str) -> None:
    ADVISORY_REFUSALS_TOTAL.labels(reason=reason).inc()


def record_advisory_approved() -> None:
    ADVISORY_APPROVED_TOTAL.inc()
