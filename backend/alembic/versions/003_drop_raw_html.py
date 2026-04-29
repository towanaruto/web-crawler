"""Drop articles.raw_html

The HTML body now lives in R2 (raw_html_r2_key). Run
src.scripts.migrate_raw_html_to_r2 BEFORE applying this migration to copy
existing rows into R2 — otherwise the data is lost.

Revision ID: 003_drop_raw_html
Revises: 002_r2_keys
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa

revision = "003_drop_raw_html"
down_revision = "002_r2_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("articles", "raw_html")


def downgrade() -> None:
    # Restore as nullable Text. Existing rows will have NULL — they would need
    # to be repopulated from R2 by hand if downgrade is ever exercised.
    op.add_column("articles", sa.Column("raw_html", sa.Text(), nullable=True))
