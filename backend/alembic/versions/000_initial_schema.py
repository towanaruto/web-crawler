"""Initial schema — tables that pre-existed migration 001.

Added retroactively so a fresh database (Neon) can run the full chain.
Pre-existing local environments where Base.metadata.create_all() bootstrapped
the schema are already at 003 (alembic_version stores only the current rev,
not a path), so this migration is a no-op for them.

Revision ID: 000_initial_schema
Revises:
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "000_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False, unique=True),
        sa.Column("source_url", sa.Text()),
        sa.Column("bio", sa.Text()),
    )

    op.create_table(
        "categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False, unique=True),
        sa.Column(
            "parent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("categories.id"),
            nullable=True,
        ),
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
    )

    op.create_table(
        "articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("slug", sa.String(512), nullable=False, unique=True),
        sa.Column("body_text", sa.Text()),
        sa.Column("body_html", sa.Text()),
        sa.Column("raw_html", sa.Text()),
        sa.Column("excerpt", sa.String(1000)),
        sa.Column("source_url", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "author_id",
            UUID(as_uuid=True),
            sa.ForeignKey("authors.id"),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            UUID(as_uuid=True),
            sa.ForeignKey("categories.id"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "crawled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("featured_image_url", sa.Text()),
        sa.Column("word_count", sa.Integer()),
    )
    # Explicit secondary index for ORDER BY published_at DESC scans.
    op.create_index(
        "ix_articles_published_at",
        "articles",
        [sa.text("published_at DESC")],
    )

    op.create_table(
        "article_tags",
        sa.Column(
            "article_id",
            UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "crawl_targets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("base_url", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "crawl_mode",
            sa.String(20),
            nullable=False,
            server_default="static",
        ),
        sa.Column("selector_config", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("max_depth", sa.Integer(), server_default="2"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
    )

    op.create_table(
        "crawl_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "target_id",
            UUID(as_uuid=True),
            sa.ForeignKey("crawl_targets.id"),
            nullable=False,
        ),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("http_status_code", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("articles_found", sa.Integer(), server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("crawl_jobs")
    op.drop_table("crawl_targets")
    op.drop_table("article_tags")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_table("articles")
    op.drop_table("tags")
    op.drop_table("categories")
    op.drop_table("authors")
