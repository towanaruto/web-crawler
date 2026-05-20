from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.engine import get_db
from src.db.models import CrawlJob, CrawlTarget
from src.scheduler.job_manager import crawl_all, crawl_target
from src.scheduler.rate_limiter import TokenBucketRateLimiter
from src.storage.r2 import build_r2_storage_from_settings

app = FastAPI(title="Web Crawler API")


class HealthResponse(BaseModel):
    status: str


class CrawlSummaryResponse(BaseModel):
    targets_crawled: int
    articles_found: int
    pages_crawled: int
    failed: int


class CrawlTargetResponse(BaseModel):
    articles: int
    pages_crawled: int
    max_depth_used: int
    keywords_used: list[str]


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


@app.post("/crawl", response_model=CrawlSummaryResponse)
def start_crawl(db: Session = Depends(get_db)) -> dict:
    return crawl_all(db)


@app.post("/crawl/{target_id}", response_model=CrawlTargetResponse)
def start_target_crawl(
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    target = db.scalar(select(CrawlTarget).where(CrawlTarget.id == target_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Crawl target not found")
    if not target.is_active:
        raise HTTPException(status_code=400, detail="Crawl target is inactive")

    rate_limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)
    r2 = build_r2_storage_from_settings(settings)
    return crawl_target(db, target, rate_limiter, r2=r2)


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
