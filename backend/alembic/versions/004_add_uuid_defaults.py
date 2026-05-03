"""Add gen_random_uuid() default to id columns

The original SQLAlchemy models declared `default=uuid.uuid4` which is a
Python-side default — only fires when SQLAlchemy itself constructs the row.
Drizzle (used by Next.js Server Actions) does not inject a value for
unspecified columns, so without a SQL-level DEFAULT every INSERT from the
frontend hits "null value in column id violates not-null constraint".

Adds DEFAULT gen_random_uuid() to the seven id columns so both Python-side
and JS-side inserts work without an explicit id. Built-in in PostgreSQL 13+
(no pgcrypto extension required); Neon uses PG 16+.

Revision ID: 004_uuid_defaults
Revises: 003_drop_raw_html
Create Date: 2026-05-03
"""
from alembic import op

revision = "004_uuid_defaults"
down_revision = "003_drop_raw_html"
branch_labels = None
depends_on = None


TABLES = (
    "authors",
    "categories",
    "tags",
    "articles",
    "crawl_targets",
    "crawl_jobs",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT gen_random_uuid()"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT")
