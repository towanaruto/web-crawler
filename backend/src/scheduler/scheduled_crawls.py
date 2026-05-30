from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import CrawlJob, CrawlTarget
from src.scheduler.crawl_jobs import create_target_crawl_job
from src.scheduler.schedules import DEFAULT_TIMEZONE, compute_next_run_at, normalize_schedule_config

logger = logging.getLogger(__name__)

OPEN_JOB_STATUSES = ("pending", "running")


@dataclass
class SchedulerTickResult:
    targets_checked: int
    targets_queued: int
    skipped_active_jobs: int
    invalid_schedules: int
    job_ids: list[uuid.UUID]


def enqueue_due_scheduled_crawls(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = 50,
) -> SchedulerTickResult:
    tick_at = _as_utc(now or datetime.now(timezone.utc))
    due_targets = list(
        db.scalars(
            select(CrawlTarget)
            .where(
                CrawlTarget.is_active.is_(True),
                CrawlTarget.schedule_enabled.is_(True),
                CrawlTarget.next_run_at.is_not(None),
                CrawlTarget.next_run_at <= tick_at,
            )
            .order_by(CrawlTarget.next_run_at.asc(), CrawlTarget.id.asc())
            .limit(limit)
        ).all()
    )

    job_ids: list[uuid.UUID] = []
    skipped_active_jobs = 0
    invalid_schedules = 0

    for target in due_targets:
        try:
            config = normalize_schedule_config(target.schedule_config)
            next_run_at = compute_next_run_at(
                config,
                after=tick_at,
                timezone_name=target.schedule_timezone or DEFAULT_TIMEZONE,
            )
        except ValueError as exc:
            logger.warning("Invalid schedule for crawl target %s: %s", target.id, exc)
            target.schedule_enabled = False
            target.next_run_at = None
            invalid_schedules += 1
            continue

        if _has_open_job(db, target):
            skipped_active_jobs += 1
            target.next_run_at = next_run_at
            continue

        job = create_target_crawl_job(db, target)
        target.last_scheduled_at = tick_at
        target.next_run_at = next_run_at
        job_ids.append(job.id)

    db.flush()
    return SchedulerTickResult(
        targets_checked=len(due_targets),
        targets_queued=len(job_ids),
        skipped_active_jobs=skipped_active_jobs,
        invalid_schedules=invalid_schedules,
        job_ids=job_ids,
    )


def _has_open_job(db: Session, target: CrawlTarget) -> bool:
    return (
        db.scalar(
            select(CrawlJob.id)
            .where(
                CrawlJob.target_id == target.id,
                CrawlJob.user_id == target.user_id,
                CrawlJob.status.in_(OPEN_JOB_STATUSES),
            )
            .limit(1)
        )
        is not None
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
