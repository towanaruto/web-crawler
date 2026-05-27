"""Add Auth0 users, invites, and user-owned crawler data.

Revision ID: 005_auth0_user_scoping
Revises: 004_uuid_defaults
Create Date: 2026-05-27
"""
from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "005_auth0_user_scoping"
down_revision = "004_uuid_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("auth0_sub", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("picture_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "invites",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("used_by_auth0_sub", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("ALTER TABLE invites ALTER COLUMN id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_invites_email", "invites", ["email"])

    bootstrap_sub = os.environ.get("AUTH0_BOOTSTRAP_SUB")
    bootstrap_email = os.environ.get("BOOTSTRAP_USER_EMAIL")
    if not bootstrap_sub or not bootstrap_email:
        raise RuntimeError(
            "AUTH0_BOOTSTRAP_SUB and BOOTSTRAP_USER_EMAIL are required for "
            "migration 005 so existing data can be assigned safely."
        )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO users (auth0_sub, email, created_at, updated_at)
            VALUES (:auth0_sub, lower(:email), now(), now())
            ON CONFLICT (auth0_sub) DO UPDATE
            SET email = excluded.email, updated_at = now()
            """
        ),
        {"auth0_sub": bootstrap_sub, "email": bootstrap_email},
    )

    op.add_column("articles", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.add_column("crawl_targets", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.add_column("crawl_jobs", sa.Column("user_id", UUID(as_uuid=True), nullable=True))

    bind.execute(
        sa.text(
            """
        UPDATE articles
        SET user_id = (SELECT id FROM users WHERE auth0_sub = :auth0_sub)
        WHERE user_id IS NULL
        """
        ),
        {"auth0_sub": bootstrap_sub},
    )
    bind.execute(
        sa.text(
            """
        UPDATE crawl_targets
        SET user_id = (SELECT id FROM users WHERE auth0_sub = :auth0_sub)
        WHERE user_id IS NULL
        """
        ),
        {"auth0_sub": bootstrap_sub},
    )
    bind.execute(
        sa.text(
            """
        UPDATE crawl_jobs
        SET user_id = (SELECT id FROM users WHERE auth0_sub = :auth0_sub)
        WHERE user_id IS NULL
        """
        ),
        {"auth0_sub": bootstrap_sub},
    )

    op.alter_column("articles", "user_id", nullable=False)
    op.alter_column("crawl_targets", "user_id", nullable=False)
    op.alter_column("crawl_jobs", "user_id", nullable=False)

    op.create_foreign_key("fk_articles_user_id", "articles", "users", ["user_id"], ["id"])
    op.create_foreign_key(
        "fk_crawl_targets_user_id", "crawl_targets", "users", ["user_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_crawl_jobs_user_id", "crawl_jobs", "users", ["user_id"], ["id"]
    )

    _drop_unique_if_exists("articles_source_url_key", "articles")
    _drop_unique_if_exists("articles_slug_key", "articles")
    _drop_unique_if_exists("crawl_targets_base_url_key", "crawl_targets")
    _drop_index_if_exists("ix_articles_source_url")
    _drop_index_if_exists("ix_articles_slug")

    op.create_unique_constraint(
        "uq_articles_user_source_url", "articles", ["user_id", "source_url"]
    )
    op.create_unique_constraint("uq_articles_user_slug", "articles", ["user_id", "slug"])
    op.create_unique_constraint(
        "uq_crawl_targets_user_base_url", "crawl_targets", ["user_id", "base_url"]
    )
    op.create_index("ix_articles_user_crawled_at", "articles", ["user_id", "crawled_at"])
    op.create_index(
        "ix_crawl_targets_user_active", "crawl_targets", ["user_id", "is_active"]
    )
    op.create_index(
        "ix_crawl_jobs_user_started_at", "crawl_jobs", ["user_id", "started_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_crawl_jobs_user_started_at", table_name="crawl_jobs")
    op.drop_index("ix_crawl_targets_user_active", table_name="crawl_targets")
    op.drop_index("ix_articles_user_crawled_at", table_name="articles")
    op.drop_constraint("uq_crawl_targets_user_base_url", "crawl_targets", type_="unique")
    op.drop_constraint("uq_articles_user_slug", "articles", type_="unique")
    op.drop_constraint("uq_articles_user_source_url", "articles", type_="unique")
    op.create_unique_constraint("crawl_targets_base_url_key", "crawl_targets", ["base_url"])
    op.create_unique_constraint("articles_slug_key", "articles", ["slug"])
    op.create_unique_constraint("articles_source_url_key", "articles", ["source_url"])

    op.drop_constraint("fk_crawl_jobs_user_id", "crawl_jobs", type_="foreignkey")
    op.drop_constraint("fk_crawl_targets_user_id", "crawl_targets", type_="foreignkey")
    op.drop_constraint("fk_articles_user_id", "articles", type_="foreignkey")
    op.drop_column("crawl_jobs", "user_id")
    op.drop_column("crawl_targets", "user_id")
    op.drop_column("articles", "user_id")
    op.drop_index("ix_invites_email", table_name="invites")
    op.drop_table("invites")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")


def _drop_unique_if_exists(name: str, table: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = '{name}'
            ) THEN
                ALTER TABLE {table} DROP CONSTRAINT {name};
            END IF;
        END $$;
        """
    )


def _drop_index_if_exists(name: str) -> None:
    op.execute(f"DROP INDEX IF EXISTS {name}")
