"""
Governance observability endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends

from backend.governance.rule_engine import GovernanceRuleEngine

router = APIRouter()


def get_governance_engine() -> GovernanceRuleEngine:
    return GovernanceRuleEngine()


@router.get(
    "/rules",
    response_model=dict[str, Any],
    summary="Return loaded governance rules",
)
def get_governance_rules(
    governance: GovernanceRuleEngine = Depends(get_governance_engine),
) -> dict[str, Any]:
    return governance.load_rules()
