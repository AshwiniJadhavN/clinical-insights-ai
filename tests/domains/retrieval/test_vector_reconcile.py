from backend.retrieval.reconcile import reconcile_vector_ids


def test_vector_reconciliation_passes_when_ids_match() -> None:
    result = reconcile_vector_ids({"doc-1", "doc-2"}, {"doc-1", "doc-2"})

    assert result.passed is True
    assert result.missing_in_pgvector == []
    assert result.missing_in_chroma == []


def test_vector_reconciliation_reports_drift() -> None:
    result = reconcile_vector_ids({"doc-1", "doc-2"}, {"doc-2", "doc-3"})

    assert result.passed is False
    assert result.missing_in_pgvector == ["doc-1"]
    assert result.missing_in_chroma == ["doc-3"]
