"""Add crawl target scheduler settings.

Revision ID: 007_crawl_target_scheduler
Revises: 006_drop_crawl_target_schedule
Create Date: 2026-05-30
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "007_crawl_target_scheduler"
down_revision = "006_drop_crawl_target_schedule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "crawl_targets",
        sa.Column("schedule_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "crawl_targets",
        sa.Column("schedule_config", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "crawl_targets",
        sa.Column(
            "schedule_timezone",
            sa.String(64),
            nullable=False,
            server_default="Asia/Tokyo",
        ),
    )
    op.add_column("crawl_targets", sa.Column("next_run_at", sa.DateTime(timezone=True)))
    op.add_column("crawl_targets", sa.Column("last_scheduled_at", sa.DateTime(timezone=True)))
    op.create_index(
        "ix_crawl_targets_schedule_due",
        "crawl_targets",
        ["schedule_enabled", "next_run_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_crawl_targets_schedule_due", table_name="crawl_targets")
    op.drop_column("crawl_targets", "last_scheduled_at")
    op.drop_column("crawl_targets", "next_run_at")
    op.drop_column("crawl_targets", "schedule_timezone")
    op.drop_column("crawl_targets", "schedule_config")
    op.drop_column("crawl_targets", "schedule_enabled")
