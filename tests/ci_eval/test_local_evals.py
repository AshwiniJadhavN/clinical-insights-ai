from evals.refusal_eval import run_refusal_eval
from evals.retrieval_eval import run_retrieval_eval


def test_retrieval_eval_finds_expected_sources() -> None:
    report = run_retrieval_eval()

    assert report.total_cases == 8
    assert report.top_1_accuracy == 1.0
    assert report.top_3_accuracy == 1.0
    assert report.missing_evidence_cases == ()


def test_refusal_eval_cases_match_expected_safety_decisions() -> None:
    report = run_refusal_eval()

    assert report.total_cases == 9
    assert report.failed_cases == 0
    assert report.passed is True