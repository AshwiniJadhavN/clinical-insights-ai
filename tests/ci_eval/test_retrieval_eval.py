from pathlib import Path

from evaluation.rag_eval import rank_documents, run_retrieval_eval


def test_retrieval_eval_passes_golden_dataset() -> None:
    result = run_retrieval_eval(
        Path("evaluation/golden_datasets/golden_retrieval.json"),
        Path("data/sample_docs"),
    )

    assert result.passed is True
    assert result.accuracy == 1.0


def test_rank_documents_orders_by_query_overlap() -> None:
    ranked = rank_documents(
        "potassium dizziness",
        {
            "cardiology.txt": "potassium dizziness lab result",
            "oncology.txt": "progression survival",
        },
    )

    assert ranked[0][0] == "cardiology.txt"
