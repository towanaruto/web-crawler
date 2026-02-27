from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import bleach
from bs4 import BeautifulSoup

from src.parser.selectors import get_selectors


def parse_article(html: str, source_url: str, selector_overrides: dict | None = None) -> dict:
    """Parse raw HTML into a structured article dict."""
    domain = urlparse(source_url).netloc
    selectors = get_selectors(domain, selector_overrides)
    soup = BeautifulSoup(html, "lxml")

    title = _extract_text(soup, selectors["title"]) or _extract_og(soup, "og:title") or ""
    body_element = soup.select_one(selectors["body"])
    body_html = _sanitize_html(str(body_element)) if body_element else ""
    body_text = body_element.get_text(separator="\n", strip=True) if body_element else ""

    excerpt = _extract_meta(soup, selectors["excerpt"]) or body_text[:200]
    author = _extract_text(soup, selectors["author"])
    published_at = _extract_datetime(soup, selectors["published_at"])
    featured_image = _extract_og(soup, "og:image") or _extract_attr(soup, selectors["featured_image"], "content")
    categories = _extract_all_text(soup, selectors["category"])
    tags = _extract_all_text(soup, selectors["tags"])
    links = _extract_links(soup, source_url)

    return {
        "title": title.strip(),
        "body_html": body_html,
        "body_text": body_text,
        "raw_html": html,
        "excerpt": excerpt[:1000],
        "source_url": source_url,
        "author_name": author,
        "published_at": published_at,
        "featured_image_url": featured_image,
        "category_names": categories,
        "tag_names": tags,
        "word_count": len(body_text.split()) if body_text else 0,
        "links": links,
    }


def _extract_text(soup: BeautifulSoup, selector: str) -> str | None:
    for sel in selector.split(","):
        el = soup.select_one(sel.strip())
        if el:
            return el.get_text(strip=True)
    return None


def _extract_all_text(soup: BeautifulSoup, selector: str) -> list[str]:
    results = []
    for sel in selector.split(","):
        for el in soup.select(sel.strip()):
            text = el.get_text(strip=True)
            if text and text not in results:
                results.append(text)
    return results


def _extract_meta(soup: BeautifulSoup, selector: str) -> str | None:
    for sel in selector.split(","):
        el = soup.select_one(sel.strip())
        if el:
            return el.get("content", el.get_text(strip=True))
    return None


def _extract_og(soup: BeautifulSoup, property_name: str) -> str | None:
    el = soup.find("meta", property=property_name)
    return el.get("content") if el else None


def _extract_attr(soup: BeautifulSoup, selector: str, attr: str) -> str | None:
    for sel in selector.split(","):
        el = soup.select_one(sel.strip())
        if el:
            return el.get(attr)
    return None


def _extract_datetime(soup: BeautifulSoup, selector: str) -> datetime | None:
    for sel in selector.split(","):
        el = soup.select_one(sel.strip())
        if el:
            dt_str = el.get("datetime") or el.get_text(strip=True)
            try:
                return datetime.fromisoformat(dt_str)
            except (ValueError, TypeError):
                pass
    return None


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if href and not href.startswith(("#", "javascript:", "mailto:")):
            full_url = urljoin(base_url, href)
            if full_url not in links:
                links.append(full_url)
    return links


ALLOWED_TAGS = [
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "a", "img", "strong", "em",
    "blockquote", "pre", "code", "figure", "figcaption",
]
ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
}


def _sanitize_html(html: str) -> str:
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
