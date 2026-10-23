"""
Query API router — POST /query.

Request flow:
  1. SafetyChecker.check_input()  — block prompt injection / harmful queries (422)
  2. QueryService.query()          — embed → retrieve → generate → audit log

HTTP status codes:
  200 — successful answer
  422 — input blocked by safety guardrails
  502 — upstream LLM provider call failed
  503 — embedder / retriever / LLM not yet ready
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.config import Settings, get_settings
from backend.guardrails.safety_checker import SafetyChecker
from backend.rag.embedder import EmbedderProtocol
from backend.rag.generator import GeneratorProtocol, create_generator
from backend.rag.retriever import RetrieverProtocol
from backend.schemas.query import QueryRequest, QueryResponse
from backend.safety.decision_engine import SafetyDecisionEngine
from backend.services.audit_service import AuditService
from backend.services.query_service import QueryService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _get_embedder_or_503() -> EmbedderProtocol:
    try:
        from backend.rag.embedder import get_embedder
        return get_embedder()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Embedding service is not ready. Please try again in a moment.",
        )


def _get_retriever_or_503(settings: Settings) -> RetrieverProtocol:
    try:
        from backend.retrieval.sync import get_sync_retriever
        return get_sync_retriever()
    except RuntimeError:
        pass

    try:
        if settings.vector_backend == "pgvector":
            from backend.rag.pgvector_retriever import get_pgvector_retriever
            return get_pgvector_retriever()
        from backend.rag.retriever import get_retriever
        return get_retriever()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Vector store is not ready. Please try again in a moment.",
        )


def _get_audit_service_optional() -> AuditService | None:
    try:
        from backend.database.session import get_session_factory
        return AuditService(get_session_factory())
    except RuntimeError:
        return None


def get_safety_checker(settings: Settings = Depends(get_settings)) -> SafetyChecker:
    return SafetyChecker(enabled=settings.enable_guardrails)


def get_query_service(settings: Settings = Depends(get_settings)) -> QueryService:
    safety_engine = SafetyDecisionEngine(confidence_threshold=settings.confidence_threshold)
    if settings.mock_llm:
        from backend.rag.generator import FakeGenerator
        return QueryService(
            settings=settings,
            embedder=_get_embedder_or_503(),
            retriever=_get_retriever_or_503(settings),
            generator=FakeGenerator(),
            safety_engine=safety_engine,
            audit_service=_get_audit_service_optional(),
        )

    try:
        generator: GeneratorProtocol = create_generator(settings)
    except ValueError as exc:
        logger.warning("LLM provider unavailable (%s) — falling back to offline fake generator", exc)
        from backend.rag.generator import FakeGenerator

        generator = FakeGenerator()
    return QueryService(
        settings=settings,
        embedder=_get_embedder_or_503(),
        retriever=_get_retriever_or_503(settings),
        generator=generator,
        safety_engine=safety_engine,
        audit_service=_get_audit_service_optional(),
    )


@router.post(
    "",
    response_model=QueryResponse,
    status_code=200,
    summary="Query clinical documents",
    description=(
        "Ask a clinical question. Input is screened by safety guardrails before "
        "the RAG pipeline runs. Each query is appended to the HIPAA audit log."
    ),
)
async def query_documents(
    body: QueryRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    checker: SafetyChecker = Depends(get_safety_checker),
) -> QueryResponse:
    safety = checker.check_input(body.question)
    if not safety.is_safe:
        raise HTTPException(status_code=422, detail=safety.reason)

    service = get_query_service(settings)
    try:
        return await service.query(body.question, body.top_k, correlation_id=getattr(request.state, "request_id", None))
    except RuntimeError as exc:
        logger.error("Query pipeline error: %s", str(exc))
        raise HTTPException(
            status_code=502,
            detail="Answer generation failed. Check LLM provider configuration.",
        )
