"""add safety metadata fields to audit log

Revision ID: 20260708_0003
Revises: 20260706_0002
Create Date: 2026-07-08
"""

from __future__ import annotations

from alembic import op

revision = "20260708_0003"
down_revision = "20260706_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS safety_decision VARCHAR(32)")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS refusal_reason VARCHAR")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(64)")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(64)")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS retrieved_doc_ids VARCHAR")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS review_required BOOLEAN NOT NULL DEFAULT FALSE")


def downgrade() -> None:
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS review_required")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS processing_time_ms")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS retrieved_doc_ids")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS prompt_version")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS correlation_id")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS refusal_reason")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS safety_decision")