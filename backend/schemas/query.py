"""
Pydantic schemas for the /query endpoint.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.health import SAFETY_DISCLAIMER


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000,
                          description="The clinical question to answer.")
    top_k: int = Field(default=5, ge=1, le=20,
                       description="Number of context chunks to retrieve from the vector store.")


class CitationInfo(BaseModel):
    doc_id: str
    original_filename: str
    chunk_index: int
    similarity_score: float = Field(ge=0.0, le=1.0)
    excerpt: str
    start_char: int = Field(default=0)
    end_char: int = Field(default=0)


class QueryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    query_id: str
    question: str
    answer: str
    citations: list[CitationInfo]
    retrieved_chunk: str | None = Field(
        default=None,
        description="Plain-text top retrieved chunk used as visible evidence.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Similarity-based retrieval confidence heuristic (not a calibrated probability).",
    )
    confidence_level: str
    evidence_status: str = Field(
        description="Retrieval evidence quality: sufficient, weak, or missing."
    )
    model_used: str
    retrieval_count: int
    created_at: datetime
    safety_decision: str = Field(description="Safety layer outcome: answer, refuse, clarify, or insufficient_evidence.")
    refusal_reason: str | None = Field(default=None, description="Reason for refusal or clarification when answer generation is blocked.")
    review_required: bool = Field(default=False, description="Whether a human reviewer should inspect this result before downstream use.")
    correlation_id: str | None = Field(default=None, description="Request correlation identifier for audit and observability.")
    disclaimer: str = SAFETY_DISCLAIMER
