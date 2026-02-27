from __future__ import annotations

import uuid
from typing import Sequence

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models import (
    Article,
    Author,
    Category,
    CrawlJob,
    CrawlTarget,
    Tag,
)


# ── Articles ──────────────────────────────────────────────

def list_articles(
    db: Session,
    *,
    category_slug: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[Sequence[Article], int]:
    query = select(Article).order_by(Article.published_at.desc().nullslast())

    if category_slug:
        query = query.join(Category).where(Category.slug == category_slug)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    articles = db.scalars(query.offset(offset).limit(limit)).all()
    return articles, total or 0


def get_article_by_slug(db: Session, slug: str) -> Article | None:
    return db.scalar(select(Article).where(Article.slug == slug))


def upsert_article(db: Session, data: dict) -> Article:
    """Insert or update an article based on source_url uniqueness."""
    existing = db.scalar(
        select(Article).where(Article.source_url == data["source_url"])
    )
    if existing:
        for key, value in data.items():
            if key not in ("id", "source_url") and value is not None:
                setattr(existing, key, value)
        db.flush()
        return existing

    if "slug" not in data or not data["slug"]:
        data["slug"] = slugify(data.get("title", str(uuid.uuid4())))

    # Ensure slug uniqueness
    base_slug = data["slug"]
    counter = 1
    while db.scalar(select(Article).where(Article.slug == data["slug"])):
        data["slug"] = f"{base_slug}-{counter}"
        counter += 1

    article = Article(**data)
    db.add(article)
    db.flush()
    return article


# ── Categories ────────────────────────────────────────────

def list_categories(db: Session) -> Sequence[Category]:
    return db.scalars(select(Category).order_by(Category.name)).all()


def get_or_create_category(db: Session, name: str) -> Category:
    slug = slugify(name)
    cat = db.scalar(select(Category).where(Category.slug == slug))
    if cat:
        return cat
    cat = Category(name=name, slug=slug)
    db.add(cat)
    db.flush()
    return cat


# ── Authors ───────────────────────────────────────────────

def get_or_create_author(db: Session, name: str) -> Author:
    slug = slugify(name)
    author = db.scalar(select(Author).where(Author.slug == slug))
    if author:
        return author
    author = Author(name=name, slug=slug)
    db.add(author)
    db.flush()
    return author


# ── Tags ──────────────────────────────────────────────────

def get_or_create_tag(db: Session, name: str) -> Tag:
    slug = slugify(name)
    tag = db.scalar(select(Tag).where(Tag.slug == slug))
    if tag:
        return tag
    tag = Tag(name=name, slug=slug)
    db.add(tag)
    db.flush()
    return tag


# ── Crawl Targets ─────────────────────────────────────────

def list_crawl_targets(db: Session, active_only: bool = True) -> Sequence[CrawlTarget]:
    query = select(CrawlTarget)
    if active_only:
        query = query.where(CrawlTarget.is_active.is_(True))
    return db.scalars(query).all()


def add_crawl_target(
    db: Session,
    base_url: str,
    crawl_mode: str = "static",
    selector_config: dict | None = None,
    max_depth: int = 2,
) -> CrawlTarget:
    existing = db.scalar(
        select(CrawlTarget).where(CrawlTarget.base_url == base_url)
    )
    if existing:
        existing.crawl_mode = crawl_mode
        if selector_config:
            existing.selector_config = selector_config
        existing.max_depth = max_depth
        existing.is_active = True
        db.flush()
        return existing

    target = CrawlTarget(
        base_url=base_url,
        crawl_mode=crawl_mode,
        selector_config=selector_config or {},
        max_depth=max_depth,
    )
    db.add(target)
    db.flush()
    return target


# ── Crawl Jobs ────────────────────────────────────────────

def create_crawl_job(db: Session, target_id: uuid.UUID, target_url: str) -> CrawlJob:
    job = CrawlJob(target_id=target_id, target_url=target_url)
    db.add(job)
    db.flush()
    return job


def update_crawl_job(db: Session, job: CrawlJob, **kwargs) -> CrawlJob:
    for key, value in kwargs.items():
        setattr(job, key, value)
    db.flush()
    return job
