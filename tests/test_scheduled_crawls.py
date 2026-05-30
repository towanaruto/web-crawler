from datetime import datetime, timedelta, timezone

from src.db.models import CrawlJob, CrawlTarget
from src.scheduler.scheduled_crawls import enqueue_due_scheduled_crawls


def test_scheduler_tick_queues_due_target(db_session, auth_user):
    now = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
    target = CrawlTarget(
        user_id=auth_user.id,
        base_url="https://example.com",
        crawl_mode="static",
        schedule_enabled=True,
        schedule_config={"type": "interval", "value": 1, "unit": "hours"},
        schedule_timezone="Asia/Tokyo",
        next_run_at=now - timedelta(minutes=5),
    )
    db_session.add(target)
    db_session.flush()

    result = enqueue_due_scheduled_crawls(db_session, now=now)

    assert result.targets_checked == 1
    assert result.targets_queued == 1
    assert result.job_ids
    assert target.last_scheduled_at == now
    assert target.next_run_at == now + timedelta(hours=1)


def test_scheduler_tick_skips_disabled_and_inactive_targets(db_session, auth_user):
    now = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
    due_config = {"type": "interval", "value": 1, "unit": "hours"}
    db_session.add_all(
        [
            CrawlTarget(
                user_id=auth_user.id,
                base_url="https://disabled.example.com",
                crawl_mode="static",
                schedule_enabled=False,
                schedule_config=due_config,
                next_run_at=now - timedelta(minutes=5),
            ),
            CrawlTarget(
                user_id=auth_user.id,
                base_url="https://inactive.example.com",
                crawl_mode="static",
                is_active=False,
                schedule_enabled=True,
                schedule_config=due_config,
                next_run_at=now - timedelta(minutes=5),
            ),
        ]
    )
    db_session.flush()

    result = enqueue_due_scheduled_crawls(db_session, now=now)

    assert result.targets_checked == 0
    assert result.targets_queued == 0


def test_scheduler_tick_skips_target_with_open_job(db_session, auth_user):
    now = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
    target = CrawlTarget(
        user_id=auth_user.id,
        base_url="https://example.com",
        crawl_mode="static",
        schedule_enabled=True,
        schedule_config={"type": "interval", "value": 1, "unit": "hours"},
        schedule_timezone="Asia/Tokyo",
        next_run_at=now - timedelta(minutes=5),
    )
    db_session.add(target)
    db_session.flush()
    db_session.add(
        CrawlJob(
            user_id=auth_user.id,
            target_id=target.id,
            target_url=target.base_url,
            status="running",
        )
    )
    db_session.flush()

    result = enqueue_due_scheduled_crawls(db_session, now=now)

    assert result.targets_checked == 1
    assert result.targets_queued == 0
    assert result.skipped_active_jobs == 1
    assert target.last_scheduled_at is None
    assert target.next_run_at == now + timedelta(hours=1)


def test_scheduler_tick_disables_invalid_schedule(db_session, auth_user):
    now = datetime(2026, 5, 30, 0, 0, tzinfo=timezone.utc)
    target = CrawlTarget(
        user_id=auth_user.id,
        base_url="https://example.com",
        crawl_mode="static",
        schedule_enabled=True,
        schedule_config={"type": "interval", "value": 3, "unit": "minutes"},
        schedule_timezone="Asia/Tokyo",
        next_run_at=now - timedelta(minutes=5),
    )
    db_session.add(target)
    db_session.flush()

    result = enqueue_due_scheduled_crawls(db_session, now=now)

    assert result.invalid_schedules == 1
    assert result.targets_queued == 0
    assert target.schedule_enabled is False
    assert target.next_run_at is None
