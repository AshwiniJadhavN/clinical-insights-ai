"""
SQLAlchemy database session factory.

DATABASE_URL switching:
  sqlite:///...    — local dev / all unit tests (no server needed)
  postgresql://... — production (set in .env / docker-compose)

Exposes:
  Base                  — DeclarativeBase; all ORM models inherit from it
  init_db(url)          — create engine + tables; called once in app lifespan
  get_session_factory() — returns the cached sessionmaker singleton
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def init_db(database_url: str) -> None:
    """
    Initialise the database engine and create all tables.

    Safe to call multiple times — create_all skips tables that already exist.
    The local import of backend.models registers all ORM models
    (Document, QueryLog, AuditLogEntry) with Base.metadata before create_all runs.
    """
    global _engine, _session_factory

    connect_args: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, connect_args=connect_args, echo=False)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    import_module("backend.models")

    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(engine)

    if engine.dialect.name == "postgresql":
        alembic_config = Config()
        alembic_config.set_main_option(
            "script_location",
            str(Path(__file__).resolve().parents[2] / "alembic"),
        )
        alembic_config.attributes["connection"] = engine
        command.upgrade(alembic_config, "head")

    _engine = engine
    _session_factory = session_factory


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory singleton. Raises if init_db() not called yet."""
    if _session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() in the application lifespan."
        )
    return _session_factory
