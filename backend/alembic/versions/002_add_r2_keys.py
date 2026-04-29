"""Add R2 storage keys to articles

raw_html_r2_key holds the R2 object key for the archived raw HTML; image_r2_keys
is a JSONB array of keys for the article's images. The legacy raw_html column
stays nullable for now and will be dropped in a later migration once existing
rows are backfilled to R2.

Revision ID: 002_r2_keys
Revises: 001_keyword_schedule
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "002_r2_keys"
down_revision = "001_keyword_schedule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("raw_html_r2_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column(
            "image_r2_keys",
            JSONB,
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.alter_column("articles", "raw_html", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.drop_column("articles", "image_r2_keys")
    op.drop_column("articles", "raw_html_r2_key")
