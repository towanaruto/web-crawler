"""One-shot script to migrate existing articles.raw_html into Cloudflare R2.

Usage:
    python -m src.scripts.migrate_raw_html_to_r2          # dry run
    python -m src.scripts.migrate_raw_html_to_r2 --apply  # actually write

Idempotent: only rows where raw_html IS NOT NULL and raw_html_r2_key IS NULL
are touched, so re-running after a partial failure is safe.

Run this BEFORE applying alembic migration 003_drop_raw_html, otherwise the
data in the raw_html column is lost forever.
"""
from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import and_, select

from src.config.settings import settings
from src.db.engine import get_session
from src.db.models import Article
from src.storage.r2 import build_r2_storage_from_settings

logger = logging.getLogger("migrate_raw_html_to_r2")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually upload and update the DB. Without this flag the script"
             " is a dry run.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    r2 = build_r2_storage_from_settings(settings)
    if r2 is None:
        logger.error(
            "R2 is not configured (R2_ACCOUNT_ID/ACCESS_KEY_ID/SECRET_ACCESS_KEY"
            "/BUCKET/PUBLIC_URL must all be set). Aborting."
        )
        return 2

    with get_session() as db:
        rows = db.scalars(
            select(Article).where(
                and_(Article.raw_html.is_not(None), Article.raw_html_r2_key.is_(None))
            )
        ).all()

        logger.info("Found %d articles to migrate", len(rows))
        if not rows:
            return 0

        if not args.apply:
            for a in rows[:5]:
                logger.info("[dry-run] would upload article %s (%d bytes)", a.id, len(a.raw_html or ""))
            if len(rows) > 5:
                logger.info("[dry-run] ... and %d more", len(rows) - 5)
            logger.info("Re-run with --apply to perform the migration.")
            return 0

        migrated = 0
        for article in rows:
            try:
                key = r2.put_raw_html(article.id, article.raw_html)
                article.raw_html_r2_key = key
                article.raw_html = None  # free the column even before drop
                db.flush()
                migrated += 1
                if migrated % 50 == 0:
                    logger.info("Migrated %d/%d", migrated, len(rows))
            except Exception:
                logger.exception("Failed to migrate article %s", article.id)
                # Continue with the rest — the script is idempotent and
                # the failed row will be retried on the next run.

        logger.info("Done. Migrated %d/%d articles.", migrated, len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
