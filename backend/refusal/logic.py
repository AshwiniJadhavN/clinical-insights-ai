"""Risk-aware refusal controls for retrieved clinical evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from backend.rag.retriever import RetrievedChunk

EvidenceStatus = Literal["missing", "weak", "sufficient"]
DEFAULT_THRESHOLD = 0.65


@dataclass(frozen=True)
class SimilarityThresholdRule:
    rule_id: str
    risk_level: str
    threshold: float
    action: str


@dataclass(frozen=True)
class RefusalDecision:
    evidence_status: EvidenceStatus
    should_refuse: bool
    threshold: float
    risk_level: str
    rule_id: str | None
    warning: str | None = None


def evidence_status(above_threshold: int, retrieved_count: int) -> EvidenceStatus:
    if retrieved_count <= 0:
        return "missing"
    if above_threshold <= 0:
        return "weak"
    return "sufficient"


def evaluate_retrieval(
    chunks: list[RetrievedChunk],
    rules_path: Path | str,
) -> RefusalDecision:
    if not chunks:
        return RefusalDecision(
            evidence_status="missing",
            should_refuse=True,
            threshold=DEFAULT_THRESHOLD,
            risk_level="UNKNOWN",
            rule_id=None,
        )

    top_chunk = chunks[0]
    risk_level = _risk_level(top_chunk)
    rule = threshold_rule_for_risk(load_similarity_threshold_rules(rules_path), risk_level)
    threshold = rule.threshold if rule else DEFAULT_THRESHOLD
    status: EvidenceStatus = "sufficient" if top_chunk.similarity_score >= threshold else "weak"
    warning = None
    if status == "weak" and rule and rule.action == "warn":
        warning = f"{rule.rule_id}: similarity below warning threshold {threshold:.2f}"

    return RefusalDecision(
        evidence_status=status,
        should_refuse=should_refuse(status),
        threshold=threshold,
        risk_level=risk_level,
        rule_id=rule.rule_id if rule else None,
        warning=warning,
    )


def should_refuse(status: EvidenceStatus) -> bool:
    return status in {"missing", "weak"}


def refusal_reason(status: EvidenceStatus) -> str:
    reasons = {
        "missing": "No relevant clinical evidence was retrieved.",
        "weak": "Retrieved clinical evidence did not meet the similarity threshold.",
        "sufficient": "Evidence meets the configured similarity threshold.",
    }
    return reasons[status]


def load_similarity_threshold_rules(rules_path: Path | str) -> list[SimilarityThresholdRule]:
    with Path(rules_path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    rules = data.get("rules", []) if isinstance(data, dict) else []
    return [
        SimilarityThresholdRule(
            rule_id=str(rule.get("rule_id") or rule.get("id")),
            risk_level=_risk_level_from_condition(str(rule.get("condition", ""))),
            threshold=float(rule["threshold"]),
            action=str(rule.get("action", "block")),
        )
        for rule in rules
        if isinstance(rule, dict) and rule.get("operator") == "similarity_threshold"
    ]


def threshold_rule_for_risk(
    rules: list[SimilarityThresholdRule],
    risk_level: str,
) -> SimilarityThresholdRule | None:
    for rule in rules:
        if rule.risk_level == risk_level:
            return rule
    return None


def _risk_level(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    raw = metadata.get("risk_level", "LOW")
    value = str(raw).strip().upper()
    return value if value in {"LOW", "MEDIUM", "HIGH"} else "LOW"


def _risk_level_from_condition(condition: str) -> str:
    for risk_level in ("HIGH", "MEDIUM", "LOW"):
        if f"'{risk_level}'" in condition or f'"{risk_level}"' in condition:
            return risk_level
    return "UNKNOWN"
