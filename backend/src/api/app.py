from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.engine import get_db
from src.db.models import CrawlJob, CrawlTarget
from src.scheduler.crawl_jobs import (
    create_all_target_crawl_jobs,
    create_target_crawl_job,
    run_queued_target_crawl,
)

app = FastAPI(title="Web Crawler API")


class HealthResponse(BaseModel):
    status: str


class CrawlJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    target_url: str
    status: str | None
    http_status_code: int | None
    error_message: str | None
    articles_found: int | None
    started_at: datetime | None
    finished_at: datetime | None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/crawl",
    response_model=list[CrawlJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
def start_crawl(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> list[CrawlJob]:
    jobs = create_all_target_crawl_jobs(db)
    db.commit()
    for job in jobs:
        background_tasks.add_task(run_queued_target_crawl, job.id)
    return jobs


@app.post(
    "/crawl/{target_id}",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_target_crawl(
    target_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CrawlJob:
    target = db.scalar(select(CrawlTarget).where(CrawlTarget.id == target_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Crawl target not found")
    if not target.is_active:
        raise HTTPException(status_code=400, detail="Crawl target is inactive")

    job = create_target_crawl_job(db, target)
    db.commit()
    background_tasks.add_task(run_queued_target_crawl, job.id)
    return job


@app.get("/crawl-jobs", response_model=list[CrawlJobResponse])
def list_crawl_jobs(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CrawlJob]:
    query = (
        select(CrawlJob)
        .order_by(CrawlJob.started_at.desc().nullslast(), CrawlJob.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(query).all())


@app.get("/crawl-jobs/{job_id}", response_model=CrawlJobResponse)
def get_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> CrawlJob:
    job = db.get(CrawlJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return job
