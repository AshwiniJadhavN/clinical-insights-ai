"""align document embedding column with pgvector

Revision ID: 20261023_0004
Revises: 20260708_0003
Create Date: 2026-10-23
"""

from __future__ import annotations

from alembic import op

revision = "20261023_0004"
down_revision = "20260708_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN embedding TYPE vector(384)
        USING CASE
            WHEN embedding IS NULL OR embedding::text = '' THEN NULL
            ELSE embedding::text::vector
        END
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN embedding TYPE TEXT
        USING embedding::text
        """
    )
