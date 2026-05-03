import logging

import requests

from src.crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)


class StaticCrawler(BaseCrawler):
    """Lightweight crawler using requests + BeautifulSoup for static HTML."""

    def __init__(self, timeout: int = 30):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.USER_AGENT})
        self._timeout = timeout

    def fetch(self, url: str) -> CrawlResult:
        try:
            resp = self._session.get(url, timeout=self._timeout)
            return CrawlResult(
                url=url,
                status_code=resp.status_code,
                html=resp.text,
            )
        except requests.RequestException as e:
            logger.error("StaticCrawler error fetching %s: %s", url, e)
            return CrawlResult(url=url, status_code=0, html="", error=str(e))

    def close(self) -> None:
        self._session.close()
