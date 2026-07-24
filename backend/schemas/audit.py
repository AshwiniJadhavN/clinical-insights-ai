"""
Pydantic schema for GET /audit responses.

from_attributes=True enables model_validate(orm_instance).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    query_id: str
    question_length: int
    answer_length: int
    retrieval_count: int
    confidence_score: float
    confidence_level: str
    model_used: str
    created_at: datetime
