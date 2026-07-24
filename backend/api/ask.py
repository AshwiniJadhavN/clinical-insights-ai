"""Root-level /ask endpoint for clinical RAG queries."""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.query import get_query_service, get_safety_checker
from backend.config import Settings, get_settings
from backend.guardrails.safety_checker import SafetyChecker
from backend.schemas.query import QueryRequest, QueryResponse
from backend.services.query_service import QueryService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/ask",
    response_model=QueryResponse,
    status_code=200,
    summary="Ask a clinical question",
    description=(
        "Root-level RAG query endpoint. The generator is not called unless at "
        "least one retrieved chunk meets the configured cosine similarity threshold."
    ),
)
async def ask_documents(
    body: QueryRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    checker: SafetyChecker = Depends(get_safety_checker),
) -> QueryResponse:
    safety = checker.check_input(body.question)
    if not safety.is_safe:
        raise HTTPException(status_code=422, detail=safety.reason)

    service: QueryService = get_query_service(settings)
    try:
        return await service.query(body.question, body.top_k, correlation_id=getattr(request.state, "request_id", None))
    except RuntimeError as exc:
        logger.error("Ask pipeline error: %s", str(exc))
        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Check LLM provider configuration.",
        )
