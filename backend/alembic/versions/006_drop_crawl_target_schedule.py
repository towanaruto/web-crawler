"""Drop unused crawl target schedule.

Revision ID: 006_drop_crawl_target_schedule
Revises: 005_auth0_user_scoping
Create Date: 2026-05-30
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "006_drop_crawl_target_schedule"
down_revision = "005_auth0_user_scoping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("crawl_targets", "schedule")


def downgrade() -> None:
    op.add_column("crawl_targets", sa.Column("schedule", sa.String(100), nullable=True))
