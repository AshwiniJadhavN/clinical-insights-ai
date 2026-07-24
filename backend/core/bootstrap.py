"""Runtime dependency wiring for the FastAPI application."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from backend.config import Settings


def initialize_runtime(app: Any, settings: Settings, logger: Any) -> None:
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    session_factory = _initialize_database(settings, logger)
    if settings.mock_llm:
        logger.info("MOCK_LLM enabled — skipping production embedder/vector startup")
        return

    from backend.rag.embedder import initialize_embedder
    app.state.embedder = initialize_embedder(settings.embedding_model)

    from backend.retrieval.sync import initialize_retrieval_sync
    app.state.retriever = initialize_retrieval_sync(settings, session_factory)

    from backend.services.sample_seed_service import seed_sample_documents
    seed_sample_documents(
        embedder=app.state.embedder,
        retriever=app.state.retriever,
        sample_dir=settings.sample_docs_directory,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def readiness_probe(app: Any) -> None:
    try:
        from backend.database.session import get_session_factory
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError("Database readiness check failed.") from exc
    app.state.retriever.count()


def _initialize_database(settings: Settings, logger: Any) -> Any | None:
    try:
        from backend.database.session import get_session_factory, init_db
        init_db(settings.database_url)
        logger.info("Database initialised")
        return get_session_factory()
    except Exception as exc:
        if settings.sync_mode == "PG_ONLY":
            raise RuntimeError("PostgreSQL is required when SYNC_MODE=PG_ONLY.") from exc
        logger.warning(
            "Database unavailable (%s) — audit logging disabled",
            type(exc).__name__,
        )
        return None
