"""add document risk level metadata

Revision ID: 20260706_0002
Revises: 20260706_0001
Create Date: 2026-07-06
"""

from __future__ import annotations

from alembic import op

revision = "20260706_0002"
down_revision = "20260706_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW'")


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS risk_level")
