"""
Pydantic schemas for operational health endpoints.
"""

from typing import Any

from pydantic import BaseModel


SAFETY_DISCLAIMER = (
    "This project is a portfolio demonstration only. It is not a medical device "
    "and must not be used for clinical decision-making."
)


class HealthResponse(BaseModel):
    status: str
    version: str
    disclaimer: str = SAFETY_DISCLAIMER
    embedder: dict[str, Any]
    vector_store: dict[str, Any]
