from src.db.models import CrawlJob, CrawlTarget
from src.scheduler import crawl_jobs


def test_run_target_crawl_job_marks_completed(db_session, monkeypatch):
    target = CrawlTarget(base_url="https://example.com", crawl_mode="static")
    db_session.add(target)
    db_session.flush()
    job = CrawlJob(target_id=target.id, target_url=target.base_url)
    db_session.add(job)
    db_session.flush()

    def fake_crawl_target(db, target, rate_limiter, r2=None):
        return {"articles": 2}

    monkeypatch.setattr(crawl_jobs, "crawl_target", fake_crawl_target)
    monkeypatch.setattr(crawl_jobs, "build_r2_storage_from_settings", lambda settings: None)

    crawl_jobs.run_target_crawl_job(db_session, job.id)

    assert job.status == "completed"
    assert job.articles_found == 2
    assert job.started_at is not None
    assert job.finished_at is not None


def test_run_target_crawl_job_marks_failed_on_exception(db_session, monkeypatch):
    target = CrawlTarget(base_url="https://example.com", crawl_mode="static")
    db_session.add(target)
    db_session.flush()
    job = CrawlJob(target_id=target.id, target_url=target.base_url)
    db_session.add(job)
    db_session.flush()

    def fake_crawl_target(db, target, rate_limiter, r2=None):
        raise RuntimeError("crawl exploded")

    monkeypatch.setattr(crawl_jobs, "crawl_target", fake_crawl_target)
    monkeypatch.setattr(crawl_jobs, "build_r2_storage_from_settings", lambda settings: None)

    crawl_jobs.run_target_crawl_job(db_session, job.id)

    assert job.status == "failed"
    assert job.error_message == "crawl exploded"
    assert job.started_at is not None
    assert job.finished_at is not None


def test_run_target_crawl_job_skips_inactive_target(db_session):
    target = CrawlTarget(
        base_url="https://example.com",
        crawl_mode="static",
        is_active=False,
    )
    db_session.add(target)
    db_session.flush()
    job = CrawlJob(target_id=target.id, target_url=target.base_url)
    db_session.add(job)
    db_session.flush()

    crawl_jobs.run_target_crawl_job(db_session, job.id)

    assert job.status == "skipped"
    assert job.error_message == "Crawl target is inactive"
    assert job.finished_at is not None
