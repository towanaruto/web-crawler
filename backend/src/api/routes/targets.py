from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.schemas import CrawlTargetCreate, CrawlTargetOut
from src.db.engine import get_db
from src.db.repository import add_crawl_target, deactivate_crawl_target, list_crawl_targets
from src.scheduler.cron_scheduler import sync_jobs

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("", response_model=List[CrawlTargetOut])
def get_targets(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    return list_crawl_targets(db, active_only=active_only)


@router.post("", response_model=CrawlTargetOut)
def create_target(
    body: CrawlTargetCreate,
    db: Session = Depends(get_db),
):
    target = add_crawl_target(
        db,
        base_url=body.base_url,
        crawl_mode=body.crawl_mode,
        max_depth=body.max_depth,
        keywords=body.keywords,
        keyword_mode=body.keyword_mode,
        schedule=body.schedule,
    )
    db.commit()
    sync_jobs()
    return target


@router.delete("/{target_id}", response_model=CrawlTargetOut)
def delete_target(
    target_id: UUID,
    db: Session = Depends(get_db),
):
    target = deactivate_crawl_target(db, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.commit()
    sync_jobs()
    return target
