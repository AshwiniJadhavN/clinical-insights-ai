from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReviewDecisionRequest(BaseModel):
    query_id: str = Field(..., min_length=1)
    reviewer_id: str = Field(..., min_length=1)
    decision: Literal["accepted", "modified", "rejected"]
    modified_answer: str | None = None
    comments: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_modified_answer(self) -> "ReviewDecisionRequest":
        if self.decision == "modified" and not (self.modified_answer and self.modified_answer.strip()):
            raise ValueError("modified_answer is required when decision='modified'.")
        return self


class ReviewDecisionResponse(BaseModel):
    query_id: str
    reviewer_id: str
    decision: Literal["accepted", "modified", "rejected"]
    created_at: datetime
    audit_file: str
