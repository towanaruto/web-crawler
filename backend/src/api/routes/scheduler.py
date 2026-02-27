from fastapi import APIRouter

from src.scheduler.cron_scheduler import get_scheduler_status, sync_jobs

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
def scheduler_status():
    """Return current scheduler status and registered jobs."""
    return get_scheduler_status()


@router.post("/sync")
def scheduler_sync():
    """Re-synchronise scheduler jobs from database targets."""
    sync_jobs()
    return get_scheduler_status()
