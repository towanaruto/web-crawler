from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from src.crawler.factory import create_crawler
from src.db.models import CrawlTarget
from src.db.repository import (
    create_crawl_job,
    get_or_create_author,
    get_or_create_category,
    get_or_create_tag,
    list_crawl_targets,
    update_crawl_job,
    upsert_article,
)
from src.parser.html_parser import parse_article
from src.parser.keyword_filter import matches_keywords
from src.scheduler.rate_limiter import TokenBucketRateLimiter
from src.scheduler.robots import can_fetch

logger = logging.getLogger(__name__)


def crawl_target(db: Session, target: CrawlTarget, rate_limiter: TokenBucketRateLimiter) -> int:
    """Crawl a single target and save discovered articles. Returns articles count."""
    job = create_crawl_job(db, target.id, target.base_url)
    update_crawl_job(db, job, status="running", started_at=datetime.now(timezone.utc))
    articles_count = 0

    try:
        if not can_fetch(target.base_url):
            update_crawl_job(
                db, job,
                status="skipped",
                error_message="Blocked by robots.txt",
                finished_at=datetime.now(timezone.utc),
            )
            db.commit()
            logger.info("Skipped %s (robots.txt)", target.base_url)
            return 0

        rate_limiter.acquire()

        with create_crawler(target.crawl_mode) as crawler:
            result = crawler.fetch(target.base_url)

        if result.error:
            update_crawl_job(
                db, job,
                status="failed",
                http_status_code=result.status_code,
                error_message=result.error,
                finished_at=datetime.now(timezone.utc),
            )
            db.commit()
            return 0

        selector_overrides = target.selector_config if target.selector_config else None
        parsed = parse_article(result.html, result.url, selector_overrides)

        target_keywords = target.keywords or []
        target_keyword_mode = target.keyword_mode or "any"
        if not matches_keywords(parsed, target_keywords, target_keyword_mode):
            logger.info("Skipped %s (keyword filter)", target.base_url)
            update_crawl_job(
                db, job,
                status="completed",
                http_status_code=result.status_code,
                articles_found=0,
                finished_at=datetime.now(timezone.utc),
            )
            db.commit()
            return 0

        if parsed["title"]:
            article_data = {
                "title": parsed["title"],
                "body_html": parsed["body_html"],
                "body_text": parsed["body_text"],
                "raw_html": parsed["raw_html"],
                "excerpt": parsed["excerpt"],
                "source_url": parsed["source_url"],
                "published_at": parsed["published_at"],
                "featured_image_url": parsed["featured_image_url"],
                "word_count": parsed["word_count"],
                "crawled_at": datetime.now(timezone.utc),
                "status": "draft",
            }

            if parsed.get("author_name"):
                author = get_or_create_author(db, parsed["author_name"])
                article_data["author_id"] = author.id

            if parsed.get("category_names"):
                category = get_or_create_category(db, parsed["category_names"][0])
                article_data["category_id"] = category.id

            article = upsert_article(db, article_data)

            if parsed.get("tag_names"):
                for tag_name in parsed["tag_names"]:
                    tag = get_or_create_tag(db, tag_name)
                    if tag not in article.tags:
                        article.tags.append(tag)

            articles_count = 1

        update_crawl_job(
            db, job,
            status="completed",
            http_status_code=result.status_code,
            articles_found=articles_count,
            finished_at=datetime.now(timezone.utc),
        )
        db.commit()

    except Exception as e:
        logger.exception("Error crawling %s", target.base_url)
        update_crawl_job(
            db, job,
            status="failed",
            error_message=str(e),
            finished_at=datetime.now(timezone.utc),
        )
        db.commit()

    return articles_count


def crawl_all(db: Session) -> dict:
    """Crawl all active targets. Returns summary stats."""
    targets = list_crawl_targets(db)
    rate_limiter = TokenBucketRateLimiter(rate=1.0, capacity=5)

    total_articles = 0
    total_targets = len(targets)
    failed = 0

    for target in targets:
        logger.info("Crawling target: %s (%s)", target.base_url, target.crawl_mode)
        count = crawl_target(db, target, rate_limiter)
        if count > 0:
            total_articles += count
        else:
            failed += 1

    return {
        "targets_crawled": total_targets,
        "articles_found": total_articles,
        "failed": failed,
    }
