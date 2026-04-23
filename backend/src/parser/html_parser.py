from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import bleach
from bs4 import BeautifulSoup, Comment

from src.parser.selectors import get_selectors
from src.parser.url_utils import canonicalize_url

# Tags whose text content is not visible prose and must be removed before any
# downstream extraction. bleach's strip=True alone is not enough: it removes
# the tag but preserves the inner text, so JSON-LD payloads and CSS rules leak
# into body_html / body_text.
_NOISE_TAGS = ("script", "style", "noscript", "template")


def _strip_noise(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()


def parse_article(html: str, source_url: str, selector_overrides: dict | None = None) -> dict:
    """Parse raw HTML into a structured article dict."""
    source_url = canonicalize_url(source_url)
    domain = urlparse(source_url).netloc
    selectors = get_selectors(domain, selector_overrides)
    soup = BeautifulSoup(html, "lxml")
    _strip_noise(soup)

    link_canonical = soup.find("link", rel="canonical")
    if link_canonical and link_canonical.get("href"):
        source_url = canonicalize_url(urljoin(source_url, link_canonical["href"]))

    title = _extract_text(soup, selectors["title"]) or _extract_og(soup, "og:title") or ""
    body_element = soup.select_one(selectors["body"])
    image_urls = _extract_images(body_element, source_url) if body_element else []
    if body_element:
        for img in body_element.find_all("img"):
            img.decompose()
    prose_html = _sanitize_html(str(body_element)) if body_element else ""
    body_html = _append_image_list(prose_html, image_urls)
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
    links: list[str] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        full = canonicalize_url(urljoin(base_url, href))
        if full not in seen:
            seen.add(full)
            links.append(full)
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


def _extract_images(body_element, base_url: str) -> list[str]:
    """Collect absolute image URLs from <img> tags, handling lazy-load attrs
    and srcset. Preserves document order, deduplicates."""
    seen: set[str] = set()
    ordered: list[str] = []
    for img in body_element.find_all("img"):
        url = _resolve_img_url(img, base_url)
        if url and url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def _resolve_img_url(img, base_url: str) -> str | None:
    # Preference order: srcset (largest) → src → data-src → data-original.
    srcset = img.get("srcset")
    if srcset:
        best = _pick_largest_srcset(srcset)
        if best:
            return urljoin(base_url, best)
    for attr in ("src", "data-src", "data-original"):
        val = img.get(attr)
        if val:
            return urljoin(base_url, val.strip())
    return None


def _pick_largest_srcset(srcset: str) -> str | None:
    """srcset syntax: '<url> <descriptor>, ...'. Pick the URL with the largest
    width descriptor (e.g. '1200w' beats '400w'). Fall back to last entry."""
    best_url = None
    best_w = -1
    for candidate in srcset.split(","):
        parts = candidate.strip().split()
        if not parts:
            continue
        url = parts[0]
        width = 0
        if len(parts) > 1 and parts[1].endswith("w"):
            try:
                width = int(parts[1][:-1])
            except ValueError:
                width = 0
        if width > best_w:
            best_w = width
            best_url = url
    return best_url


def _append_image_list(prose_html: str, urls: list[str]) -> str:
    if not urls:
        return prose_html
    items = "".join(f'<li><img src="{url}" alt=""></li>' for url in urls)
    return f"{prose_html.rstrip()}\n<ul>{items}</ul>"
