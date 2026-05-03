"""
Site-specific CSS selectors for parsing articles.

Each config is a dict with keys matching the fields of an article.
Values are CSS selectors used by BeautifulSoup's select/select_one.
"""
from __future__ import annotations

DEFAULT_SELECTORS = {
    "title": "h1",
    "body": "article, .post-content, .entry-content, .article-body, main",
    "author": ".author, .byline, [rel='author']",
    "published_at": "time[datetime], .published, .post-date",
    "category": ".category, .post-category, [rel='tag']",
    "tags": ".tag, .post-tag, [rel='tag']",
    "featured_image": "meta[property='og:image']",
    "excerpt": "meta[name='description'], meta[property='og:description']",
    "links": "a[href]",
}


# Site-specific overrides keyed by domain
SITE_SELECTORS: dict[str, dict[str, str]] = {}


def get_selectors(domain: str | None = None, overrides: dict | None = None) -> dict[str, str]:
    """Get CSS selectors for a given domain, with optional overrides."""
    selectors = dict(DEFAULT_SELECTORS)
    if domain and domain in SITE_SELECTORS:
        selectors.update(SITE_SELECTORS[domain])
    if overrides:
        selectors.update(overrides)
    return selectors
