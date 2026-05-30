from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.invites import consume_verified_invite, verify_invite
from src.config.settings import settings
from src.db.engine import get_db
from src.db.models import CrawlJob, CrawlTarget
from src.scheduler.crawl_jobs import (
    create_all_target_crawl_jobs,
    create_target_crawl_job,
    run_queued_target_crawl,
)
from src.scheduler.scheduled_crawls import enqueue_due_scheduled_crawls

app = FastAPI(title="Web Crawler API")


class HealthResponse(BaseModel):
    status: str


class CrawlSummaryResponse(BaseModel):
    user_id: uuid.UUID
    targets_queued: int
    job_ids: list[uuid.UUID]


class CrawlJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    target_id: uuid.UUID
    target_url: str
    status: str | None
    http_status_code: int | None
    error_message: str | None
    articles_found: int | None
    started_at: datetime | None
    finished_at: datetime | None


class SchedulerTickResponse(BaseModel):
    targets_checked: int
    targets_queued: int
    skipped_active_jobs: int
    invalid_schedules: int
    job_ids: list[uuid.UUID]


CrawlTargetResponse = CrawlJobResponse


class UserScopedRequest(BaseModel):
    user_id: uuid.UUID


class InviteVerifyRequest(BaseModel):
    email: str
    access_code: str
    provider: str | None = None


class InviteConsumeRequest(BaseModel):
    email: str
    auth0_sub: str | None = None
    provider: str | None = None


class InviteResponse(BaseModel):
    ok: bool


def require_internal_api_key(
    x_internal_api_key: str | None = Header(default=None),
) -> None:
    expected = settings.BACKEND_API_TOKEN
    if not expected:
        return
    if x_internal_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/crawl",
    response_model=CrawlSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_crawl(
    background_tasks: BackgroundTasks,
    body: UserScopedRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_api_key),
) -> CrawlSummaryResponse:
    jobs = create_all_target_crawl_jobs(db, user_id=body.user_id)
    db.commit()
    for job in jobs:
        background_tasks.add_task(run_queued_target_crawl, job.id)
    return CrawlSummaryResponse(
        user_id=body.user_id,
        targets_queued=len(jobs),
        job_ids=[job.id for job in jobs],
    )


@app.post(
    "/crawl/{target_id}",
    response_model=CrawlTargetResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_target_crawl(
    target_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Query(...),
    _: None = Depends(require_internal_api_key),
) -> dict:
    target = db.scalar(
        select(CrawlTarget).where(
            CrawlTarget.id == target_id,
            CrawlTarget.user_id == user_id,
        )
    )
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
    user_id: uuid.UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: None = Depends(require_internal_api_key),
) -> list[CrawlJob]:
    query = (
        select(CrawlJob)
        .where(CrawlJob.user_id == user_id)
        .order_by(CrawlJob.started_at.desc().nullslast(), CrawlJob.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(query).all())


@app.get("/crawl-jobs/{job_id}", response_model=CrawlJobResponse)
def get_crawl_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Query(...),
    _: None = Depends(require_internal_api_key),
) -> CrawlJob:
    job = db.scalar(select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.user_id == user_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return job


@app.post(
    "/scheduler/tick",
    response_model=SchedulerTickResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def scheduler_tick(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    _: None = Depends(require_internal_api_key),
) -> SchedulerTickResponse:
    result = enqueue_due_scheduled_crawls(db, limit=limit)
    db.commit()
    for job_id in result.job_ids:
        background_tasks.add_task(run_queued_target_crawl, job_id)
    return SchedulerTickResponse(
        targets_checked=result.targets_checked,
        targets_queued=result.targets_queued,
        skipped_active_jobs=result.skipped_active_jobs,
        invalid_schedules=result.invalid_schedules,
        job_ids=result.job_ids,
    )


@app.post("/auth/invites/verify", response_model=InviteResponse)
def verify_access_code(
    body: InviteVerifyRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_api_key),
) -> InviteResponse:
    invite = verify_invite(db, email=body.email, access_code=body.access_code)
    if invite is None:
        raise HTTPException(status_code=403, detail="Invalid access code")
    db.commit()
    return InviteResponse(ok=True)


@app.post("/auth/invites/consume", response_model=InviteResponse)
def consume_access_code(
    body: InviteConsumeRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_api_key),
) -> InviteResponse:
    invite = consume_verified_invite(
        db,
        email=body.email,
        auth0_sub=body.auth0_sub,
    )
    if invite is None:
        raise HTTPException(status_code=403, detail="Invite not authorized")
    db.commit()
    return InviteResponse(ok=True)
