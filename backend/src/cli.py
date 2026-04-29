import logging
import uuid

import typer
from sqlalchemy import select

from src.config.settings import settings
from src.db.engine import get_session
from src.db.models import Base, CrawlTarget
from src.db.engine import engine
from src.db.repository import add_crawl_target, list_crawl_targets
from src.scheduler.job_manager import crawl_all, crawl_target as run_crawl_target
from src.scheduler.rate_limiter import TokenBucketRateLimiter
from src.storage.r2 import build_r2_storage_from_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = typer.Typer(help="Web Crawler CLI")


@app.command()
def init_db():
    """Create all database tables."""
    if settings.DATABASE_URL:
        typer.echo(
            "DATABASE_URL is set — schema is managed by Alembic.\n"
            "Run: alembic upgrade head"
        )
        raise typer.Exit(code=1)
    Base.metadata.create_all(engine)
    typer.echo("Database tables created.")


@app.command()
def add_target(
    url: str,
    mode: str = typer.Option("static", help="Crawl mode: static or dynamic"),
    max_depth: int = typer.Option(2, help="Max crawl depth"),
    keywords: str = typer.Option("", help="Comma-separated keywords for filtering"),
    keyword_mode: str = typer.Option("any", help="Keyword match mode: any or all"),
    schedule: str = typer.Option(None, help='Cron expression, e.g. "0 */6 * * *"'),
):
    """Add a crawl target URL."""
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
    with get_session() as db:
        target = add_crawl_target(
            db, url,
            crawl_mode=mode,
            max_depth=max_depth,
            keywords=kw_list,
            keyword_mode=keyword_mode,
            schedule=schedule,
        )
        typer.echo(f"Added target: {target.base_url} (mode={target.crawl_mode})")
        if kw_list:
            typer.echo(f"  keywords={kw_list}  mode={keyword_mode}")
        if schedule:
            typer.echo(f"  schedule={schedule}")


@app.command()
def list_targets():
    """List all active crawl targets."""
    with get_session() as db:
        targets = list_crawl_targets(db)
        if not targets:
            typer.echo("No active targets.")
            return
        for t in targets:
            parts = [f"  [{t.crawl_mode}] {t.base_url}"]
            if t.keywords:
                parts.append(f"  keywords={t.keywords}")
            if t.schedule:
                parts.append(f"  schedule={t.schedule}")
            typer.echo("".join(parts))


@app.command()
def crawl():
    """Crawl all active targets."""
    with get_session() as db:
        result = crawl_all(db)
        typer.echo(
            f"Done. Targets: {result['targets_crawled']}, "
            f"Articles: {result['articles_found']}, "
            f"Failed: {result['failed']}"
        )


@app.command("crawl-target")
def crawl_one(target_id: str):
    """Crawl a single target by UUID. Used by workflow_dispatch from the UI."""
    try:
        tid = uuid.UUID(target_id)
    except ValueError:
        typer.echo(f"Invalid UUID: {target_id}", err=True)
        raise typer.Exit(code=2)

    rate_limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)
    r2 = build_r2_storage_from_settings(settings)

    with get_session() as db:
        target = db.scalar(select(CrawlTarget).where(CrawlTarget.id == tid))
        if target is None:
            typer.echo(f"Target not found: {tid}", err=True)
            raise typer.Exit(code=1)
        if not target.is_active:
            typer.echo(f"Target is inactive: {tid}", err=True)
            raise typer.Exit(code=1)
        stats = run_crawl_target(db, target, rate_limiter, r2=r2)
        typer.echo(
            f"Done. Pages: {stats['pages_crawled']}, "
            f"Articles: {stats['articles']}"
        )


if __name__ == "__main__":
    app()
