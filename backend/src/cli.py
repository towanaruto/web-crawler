import logging

import typer

from src.db.engine import get_session
from src.db.models import Base
from src.db.engine import engine
from src.db.repository import add_crawl_target, list_crawl_targets
from src.scheduler.job_manager import crawl_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = typer.Typer(help="Web Crawler CLI")


@app.command()
def init_db():
    """Create all database tables."""
    Base.metadata.create_all(engine)
    typer.echo("Database tables created.")


@app.command()
def add_target(
    url: str,
    mode: str = typer.Option("static", help="Crawl mode: static or dynamic"),
    max_depth: int = typer.Option(2, help="Max crawl depth"),
):
    """Add a crawl target URL."""
    with get_session() as db:
        target = add_crawl_target(db, url, crawl_mode=mode, max_depth=max_depth)
        typer.echo(f"Added target: {target.base_url} (mode={target.crawl_mode})")


@app.command()
def list_targets():
    """List all active crawl targets."""
    with get_session() as db:
        targets = list_crawl_targets(db)
        if not targets:
            typer.echo("No active targets.")
            return
        for t in targets:
            typer.echo(f"  [{t.crawl_mode}] {t.base_url}")


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


if __name__ == "__main__":
    app()
