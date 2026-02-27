"""Add keywords, keyword_mode, schedule to crawl_targets

Revision ID: 001_keyword_schedule
Revises:
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001_keyword_schedule"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("crawl_targets", sa.Column("keywords", JSONB, server_default="[]"))
    op.add_column("crawl_targets", sa.Column("keyword_mode", sa.String(10), server_default="any"))
    op.add_column("crawl_targets", sa.Column("schedule", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("crawl_targets", "schedule")
    op.drop_column("crawl_targets", "keyword_mode")
    op.drop_column("crawl_targets", "keywords")
