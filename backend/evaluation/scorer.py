"""
Confidence scorer for RAG query results.

Classification bands (all-MiniLM-L6-v2 cosine similarity space):
  high:   score >= 0.70
  medium: score >= 0.45
  low:    score  < 0.45
  none:   no chunks
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.rag.retriever import RetrievedChunk

HIGH_THRESHOLD: float = 0.70
MEDIUM_THRESHOLD: float = 0.45


@dataclass(frozen=True)
class ConfidenceResult:
    score: float
    level: str
    retrieved_count: int
    above_threshold: int


def compute_confidence(
    chunks: list[RetrievedChunk],
    min_threshold: float = 0.6,
) -> ConfidenceResult:
    if not chunks:
        return ConfidenceResult(score=0.0, level="none", retrieved_count=0, above_threshold=0)
    scores = [c.similarity_score for c in chunks]
    mean_score = sum(scores) / len(scores)
    above = sum(1 for s in scores if s >= min_threshold)
    if mean_score >= HIGH_THRESHOLD:
        level = "high"
    elif mean_score >= MEDIUM_THRESHOLD:
        level = "medium"
    else:
        level = "low"
    return ConfidenceResult(score=round(mean_score, 4), level=level,
                            retrieved_count=len(chunks), above_threshold=above)
