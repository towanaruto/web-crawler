from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright, Browser

from src.crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)


class DynamicCrawler(BaseCrawler):
    """Playwright-based crawler for JavaScript-rendered (SPA) pages."""

    def __init__(self, timeout: int = 30_000):
        self._pw = sync_playwright().start()
        self._browser: Browser = self._pw.chromium.launch(headless=True)
        self._timeout = timeout

    def fetch(self, url: str) -> CrawlResult:
        page = self._browser.new_page(user_agent=self.USER_AGENT)
        try:
            response = page.goto(url, wait_until="networkidle", timeout=self._timeout)
            status_code = response.status if response else 0
            html = page.content()
            return CrawlResult(url=url, status_code=status_code, html=html)
        except Exception as e:
            logger.error("DynamicCrawler error fetching %s: %s", url, e)
            return CrawlResult(url=url, status_code=0, html="", error=str(e))
        finally:
            page.close()

    def close(self) -> None:
        self._browser.close()
        self._pw.stop()
