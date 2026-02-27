from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.db.engine import SessionLocal
from src.db.models import CrawlTarget
from src.db.repository import list_crawl_targets
from src.scheduler.job_manager import crawl_target
from src.scheduler.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_rate_limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)


def start_scheduler() -> None:
    """Start the background scheduler and load jobs from DB."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.start()
    logger.info("CronScheduler started")
    sync_jobs()


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("CronScheduler shut down")
        _scheduler = None


def sync_jobs() -> None:
    """Synchronise APScheduler jobs with the database.

    Removes stale jobs and adds/updates scheduled targets.
    """
    if _scheduler is None:
        return

    db = SessionLocal()
    try:
        targets = list_crawl_targets(db, active_only=True)

        scheduled_ids: set[str] = set()
        for target in targets:
            if not target.schedule:
                continue
            job_id = f"crawl_{target.id}"
            scheduled_ids.add(job_id)

            try:
                trigger = CronTrigger.from_crontab(target.schedule)
            except ValueError:
                logger.warning("Invalid cron expression '%s' for target %s", target.schedule, target.base_url)
                continue

            existing_job = _scheduler.get_job(job_id)
            if existing_job:
                existing_job.reschedule(trigger)
                logger.info("Rescheduled job %s (%s)", job_id, target.schedule)
            else:
                _scheduler.add_job(
                    _run_scheduled_crawl,
                    trigger=trigger,
                    id=job_id,
                    args=[str(target.id)],
                    max_instances=1,
                    coalesce=True,
                    replace_existing=True,
                    name=f"crawl {target.base_url}",
                )
                logger.info("Added job %s — cron %s", job_id, target.schedule)

        # Remove jobs for targets that no longer have a schedule
        for job in _scheduler.get_jobs():
            if job.id.startswith("crawl_") and job.id not in scheduled_ids:
                job.remove()
                logger.info("Removed stale job %s", job.id)
    finally:
        db.close()


def _run_scheduled_crawl(target_id: str) -> None:
    """APScheduler callback — crawl a single target using its own session."""
    db = SessionLocal()
    try:
        from sqlalchemy import select
        from src.db.models import CrawlTarget
        target = db.scalar(select(CrawlTarget).where(CrawlTarget.id == target_id))
        if target is None or not target.is_active:
            logger.warning("Scheduled target %s not found or inactive", target_id)
            return
        logger.info("Scheduled crawl starting: %s", target.base_url)
        crawl_target(db, target, _rate_limiter)
    except Exception:
        logger.exception("Scheduled crawl failed for target %s", target_id)
    finally:
        db.close()


def get_scheduler_status() -> dict:
    """Return current scheduler status and job list."""
    if _scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": _scheduler.running,
        "jobs": jobs,
    }
