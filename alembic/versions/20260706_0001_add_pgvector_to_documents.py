"""add pgvector embeddings to documents

Revision ID: 20260706_0001
Revises:
Create Date: 2026-07-06
"""

from __future__ import annotations

from alembic import op

revision = "20260706_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_text TEXT")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedding vector(384)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_documents_embedding_hnsw
        ON documents
        USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_documents_embedding_hnsw")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS content_text")
