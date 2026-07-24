"""Vector-store reconciliation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationResult:
    passed: bool
    chroma_count: int
    pgvector_count: int
    missing_in_pgvector: list[str]
    missing_in_chroma: list[str]


def reconcile_vector_ids(
    chroma_ids: set[str],
    pgvector_ids: set[str],
) -> ReconciliationResult:
    missing_in_pgvector = sorted(chroma_ids - pgvector_ids)
    missing_in_chroma = sorted(pgvector_ids - chroma_ids)
    return ReconciliationResult(
        passed=not missing_in_pgvector and not missing_in_chroma,
        chroma_count=len(chroma_ids),
        pgvector_count=len(pgvector_ids),
        missing_in_pgvector=missing_in_pgvector,
        missing_in_chroma=missing_in_chroma,
    )
