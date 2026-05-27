from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.engine import get_session
from src.db.models import CrawlJob, CrawlTarget
from src.db.repository import create_crawl_job, list_crawl_targets, update_crawl_job
from src.scheduler.job_manager import crawl_target
from src.scheduler.rate_limiter import TokenBucketRateLimiter
from src.storage.r2 import build_r2_storage_from_settings

logger = logging.getLogger(__name__)

# Crawl job status meanings:
# pending: API accepted the request and queued background execution.
# running: background execution has started for the target.
# completed: background execution finished without a fatal target-level error.
# failed: background execution hit a fatal target-level error.
# skipped: target could not be crawled by policy/state, such as inactive target.


def create_target_crawl_job(db: Session, target: CrawlTarget) -> CrawlJob:
    return create_crawl_job(db, target.id, target.base_url)


def create_all_target_crawl_jobs(db: Session) -> list[CrawlJob]:
    return [create_target_crawl_job(db, target) for target in list_crawl_targets(db)]


def run_queued_target_crawl(job_id: uuid.UUID) -> None:
    """Run a queued crawl job in a fresh DB session.

    This keeps the API request/response lifecycle separate from the long-running
    crawler and gives the implementation a narrow boundary for a future worker queue.
    """
    with get_session() as db:
        run_target_crawl_job(db, job_id)


def run_target_crawl_job(db: Session, job_id: uuid.UUID) -> None:
    job = db.get(CrawlJob, job_id)
    if job is None:
        logger.error("Queued crawl job not found: %s", job_id)
        return

    target = db.scalar(select(CrawlTarget).where(CrawlTarget.id == job.target_id))
    if target is None:
        update_crawl_job(
            db,
            job,
            status="failed",
            error_message="Crawl target not found",
            finished_at=datetime.now(timezone.utc),
        )
        return

    if not target.is_active:
        update_crawl_job(
            db,
            job,
            status="skipped",
            error_message="Crawl target is inactive",
            finished_at=datetime.now(timezone.utc),
        )
        return

    update_crawl_job(
        db,
        job,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.commit()

    try:
        rate_limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)
        r2 = build_r2_storage_from_settings(settings)
        stats = crawl_target(db, target, rate_limiter, r2=r2)
    except Exception as exc:
        logger.exception("Queued crawl job failed: %s", job_id)
        db.rollback()
        job = db.get(CrawlJob, job_id)
        if job is not None:
            update_crawl_job(
                db,
                job,
                status="failed",
                error_message=str(exc)[:500],
                finished_at=datetime.now(timezone.utc),
            )
        return

    job = db.get(CrawlJob, job_id)
    if job is not None:
        update_crawl_job(
            db,
            job,
            status="completed",
            articles_found=stats["articles"],
            finished_at=datetime.now(timezone.utc),
        )
