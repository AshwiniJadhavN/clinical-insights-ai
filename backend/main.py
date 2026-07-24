"""
FastAPI application factory.

Lifespan handler initialises all expensive resources in order:
  1. Database (SQLAlchemy + create_all) — graceful if PostgreSQL unavailable
  2. Embedding model (sentence-transformers, ~500ms)
  3. ChromaDB vector store

api-design: /health surfaces per-subsystem readiness for deploy tooling.

To run:
    uvicorn backend.main:app --reload --port 8000
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uuid

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from backend.config import get_settings
from backend.middleware.authentication import AuthenticationMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.audit.search import (
    MAX_AUDIT_SEARCH_RESULTS,
    require_audit_search_access,
    search_audit_trail,
)
from backend.core.bootstrap import initialize_runtime, readiness_probe as probe_readiness
from backend.schemas.health import HealthResponse
from backend.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

CLINICAL_INSIGHTS_APP_INFO = Gauge(
    "clinical_insights_app_info",
    "Application version info.",
    ["version"],
)
CLINICAL_INSIGHTS_INDEXED_CHUNKS = Gauge(
    "clinical_insights_indexed_chunks",
    "Indexed vector chunks.",
)
CLINICAL_INSIGHTS_HTTP_REQUESTS = Gauge(
    "clinical_insights_http_requests_total",
    "HTTP requests handled.",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    initialize_runtime(app, settings, logger)
    yield
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Clinical document analysis powered by Retrieval-Augmented Generation (RAG). "
            "Upload clinical PDFs, ask questions, get cited answers with confidence scores."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        AuthenticationMiddleware,
        api_key=settings.auth_api_key,
    )
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        request.app.state.request_count = getattr(request.app.state, "request_count", 0) + 1
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "HTTP request completed",
            extra={"request_id": request_id, "correlation_id": request_id},
        )
        return response

    from backend.api import agentic, ask, audit, documents, governance, query, review
    from backend.testing_ai import routes as testing_ai_routes
    app.include_router(agentic.router, prefix="/advisory", tags=["Advisory Automation"])
    app.include_router(
        agentic.router,
        prefix="/agentic",
        tags=["Advisory Automation"],
        include_in_schema=False,
    )
    app.include_router(ask.router, tags=["Query"])
    app.include_router(governance.router, prefix="/governance", tags=["Governance"])
    app.include_router(documents.router, prefix="/documents", tags=["Documents"])
    app.include_router(query.router, prefix="/query", tags=["Query"])
    app.include_router(audit.router, prefix="/audit", tags=["Audit"])
    app.include_router(review.router, prefix="/reviews", tags=["Review"])
    app.include_router(testing_ai_routes.router, prefix="/testing-ai", tags=["Testing AI"])

    @app.get("/health/live", response_model=dict[str, str], tags=["Health"])
    async def liveness_check() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready", response_model=dict[str, str], tags=["Health"])
    async def readiness_check(request: Request) -> dict[str, str]:
        try:
            await asyncio.wait_for(asyncio.to_thread(_readiness_probe, request), timeout=10.0)
        except Exception:
            raise HTTPException(status_code=503, detail="Service is not ready.")
        return {"status": "ready"}

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check(request: Request) -> HealthResponse:
        result: dict = {"status": "healthy", "version": settings.app_version}

        try:
            emb = request.app.state.embedder
            result["embedder"] = {
                "model": emb.model_name,
                "dimension": emb.dimension,
                "status": "ready",
            }
        except AttributeError:
            result["embedder"] = {"status": "not initialized"}

        try:
            ret = request.app.state.retriever
            result["vector_store"] = {
                "indexed_chunks": ret.count(),
                "status": "ready",
            }
        except AttributeError:
            result["vector_store"] = {"status": "not initialized"}

        return HealthResponse(**result)

    @app.get("/metrics", tags=["Monitoring"])
    async def metrics(request: Request) -> Response:
        try:
            indexed_chunks = request.app.state.retriever.count()
        except AttributeError:
            indexed_chunks = 0

        request_count = getattr(request.app.state, "request_count", 0)
        CLINICAL_INSIGHTS_APP_INFO.labels(version=settings.app_version).set(1)
        CLINICAL_INSIGHTS_INDEXED_CHUNKS.set(indexed_chunks)
        CLINICAL_INSIGHTS_HTTP_REQUESTS.set(request_count)
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.get(
        "/audit/search",
        response_model=list[dict],
        tags=["Audit"],
    )
    async def audit_search(
        request: Request,
        audit_id: str | None = None,
        input_hash: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        approval_status: str | None = Query(default=None),
        limit: int = Query(default=MAX_AUDIT_SEARCH_RESULTS, ge=1, le=MAX_AUDIT_SEARCH_RESULTS),
        x_audit_api_key: str | None = Header(default=None, alias="X-Audit-API-Key"),
    ) -> list[dict]:
        require_audit_search_access(request, settings, x_audit_api_key)
        try:
            return search_audit_trail(
                trail_directory=Path(settings.audit_trail_directory),
                audit_id=audit_id,
                input_hash=input_hash,
                start_time=start_time,
                end_time=end_time,
                approval_status=approval_status,
                limit=limit,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return app


def _readiness_probe(request: Request) -> None:
    probe_readiness(request.app)


app = create_app()
