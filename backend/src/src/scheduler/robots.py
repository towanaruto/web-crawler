from __future__ import annotations

from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests

_cache: dict[str, RobotFileParser] = {}


def can_fetch(url: str, user_agent: str = "WebCrawlerBot/1.0") -> bool:
    """Check if the given URL is allowed by the site's robots.txt."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    if robots_url not in _cache:
        rp = RobotFileParser()
        try:
            resp = requests.get(robots_url, timeout=10)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                # If robots.txt is missing, allow everything
                rp.parse([])
        except requests.RequestException:
            rp.parse([])
        _cache[robots_url] = rp

    return _cache[robots_url].can_fetch(user_agent, url)


def get_crawl_delay(url: str, user_agent: str = "WebCrawlerBot/1.0") -> float | None:
    """Return crawl-delay if specified in robots.txt."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    if robots_url in _cache:
        return _cache[robots_url].crawl_delay(user_agent)
    return None
