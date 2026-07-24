"""
ORM model registry.

Importing this module registers all table mappings with Base.metadata,
which is required for Base.metadata.create_all() and Alembic autogenerate.
"""

from __future__ import annotations

from backend.models.audit_log import AuditLogEntry  # noqa: F401
from backend.models.document import Document  # noqa: F401
from backend.models.query_log import QueryLog  # noqa: F401

__all__ = ["AuditLogEntry", "Document", "QueryLog"]
