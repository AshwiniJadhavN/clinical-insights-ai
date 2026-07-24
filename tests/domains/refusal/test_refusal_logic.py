from backend.rag.retriever import RetrievedChunk
from backend.refusal.logic import (
    evaluate_retrieval,
    evidence_status,
    load_similarity_threshold_rules,
    refusal_reason,
    should_refuse,
    threshold_rule_for_risk,
)


def test_refusal_logic_classifies_missing_weak_and_sufficient_evidence() -> None:
    assert evidence_status(above_threshold=0, retrieved_count=0) == "missing"
    assert evidence_status(above_threshold=0, retrieved_count=2) == "weak"
    assert evidence_status(above_threshold=1, retrieved_count=2) == "sufficient"


def test_refusal_logic_refuses_missing_or_weak_only() -> None:
    assert should_refuse("missing") is True
    assert should_refuse("weak") is True
    assert should_refuse("sufficient") is False


def test_refusal_logic_explains_each_status() -> None:
    assert "No relevant" in refusal_reason("missing")
    assert "threshold" in refusal_reason("weak")
    assert "meets" in refusal_reason("sufficient")


def test_refusal_logic_loads_dynamic_threshold_rules() -> None:
    rules = load_similarity_threshold_rules("backend/governance/rules.yml")

    high_rule = threshold_rule_for_risk(rules, "HIGH")
    assert high_rule is not None
    assert high_rule.rule_id == "THRESH_001"
    assert high_rule.threshold == 0.92


def test_refusal_logic_applies_high_risk_threshold() -> None:
    decision = evaluate_retrieval(
        [
            RetrievedChunk(
                text="oncology treatment details",
                doc_id="doc-1",
                chunk_index=0,
                original_filename="oncology.txt",
                similarity_score=0.9,
                metadata={"risk_level": "HIGH"},
            )
        ],
        "backend/governance/rules.yml",
    )

    assert decision.evidence_status == "weak"
    assert decision.should_refuse is True
    assert decision.threshold == 0.92
    assert decision.rule_id == "THRESH_001"


def test_refusal_logic_normalizes_risk_level_casing_and_whitespace() -> None:
    for variant in ("high", "High", " HIGH ", " high "):
        decision = evaluate_retrieval(
            [
                RetrievedChunk(
                    text="oncology treatment details",
                    doc_id="doc-norm",
                    chunk_index=0,
                    original_filename="oncology.txt",
                    similarity_score=0.90,
                    metadata={"risk_level": variant},
                )
            ],
            "backend/governance/rules.yml",
        )
        assert decision.threshold == 0.92, f"Expected HIGH threshold for risk_level={variant!r}"
        assert decision.should_refuse is True, f"Expected refusal for risk_level={variant!r}"
        assert decision.risk_level == "HIGH", f"Expected normalized risk_level='HIGH' for {variant!r}"


def test_refusal_logic_warns_for_medium_risk_below_threshold() -> None:
    decision = evaluate_retrieval(
        [
            RetrievedChunk(
                text="potassium result",
                doc_id="doc-2",
                chunk_index=0,
                original_filename="lab.txt",
                similarity_score=0.75,
                metadata={"risk_level": "MEDIUM"},
            )
        ],
        "backend/governance/rules.yml",
    )

    assert decision.evidence_status == "weak"
    assert decision.warning is not None


def test_refusal_logic_handles_missing_and_unknown_metadata() -> None:
    missing = evaluate_retrieval([], "backend/governance/rules.yml")
    unknown = evaluate_retrieval(
        [
            RetrievedChunk(
                text="general clinical text",
                doc_id="doc-3",
                chunk_index=0,
                original_filename="general.txt",
                similarity_score=0.7,
                metadata={"risk_level": "INVALID"},
            )
        ],
        "backend/governance/rules.yml",
    )

    assert missing.evidence_status == "missing"
    assert unknown.evidence_status == "sufficient"
    assert unknown.risk_level == "LOW"


def test_refusal_logic_defaults_when_no_threshold_rule_matches(tmp_path) -> None:
    rules_file = tmp_path / "rules.yml"
    rules_file.write_text(
        """
rules:
  - rule_id: THRESH_UNKNOWN
    operator: similarity_threshold
    condition: "metadata.risk_level == 'UNKNOWN'"
    threshold: 0.99
    action: block
""",
        encoding="utf-8",
    )
    rules = load_similarity_threshold_rules(rules_file)
    decision = evaluate_retrieval(
        [
            RetrievedChunk(
                text="general clinical text",
                doc_id="doc-4",
                chunk_index=0,
                original_filename="general.txt",
                similarity_score=0.66,
                metadata={"risk_level": "LOW"},
            )
        ],
        rules_file,
    )

    assert threshold_rule_for_risk(rules, "HIGH") is None
    assert decision.threshold == 0.65
    assert decision.evidence_status == "sufficient"
