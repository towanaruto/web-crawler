from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright, Browser, TimeoutError as PlaywrightTimeout

from src.crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)


class DynamicCrawler(BaseCrawler):
    """Playwright-based crawler for JavaScript-rendered (SPA) pages.

    Two-phase wait strategy:
      1. ``goto(wait_until="domcontentloaded")`` — guaranteed to fire on any
         valid response, gets the initial DOM. Fast and reliable.
      2. Best-effort ``wait_for_load_state("networkidle")`` with a short cap
         so React/Vue hydration has time to render content. Tracking-heavy
         sites (GA, session keep-alive) never reach networkidle, so we
         tolerate a timeout and proceed with the DOM we already have.
    """

    HYDRATION_WAIT_MS = 5_000

    def __init__(self, timeout: int = 30_000):
        self._pw = sync_playwright().start()
        self._browser: Browser = self._pw.chromium.launch(headless=True)
        self._timeout = timeout

    def fetch(self, url: str) -> CrawlResult:
        page = self._browser.new_page(user_agent=self.USER_AGENT)
        try:
            response = page.goto(
                url, wait_until="domcontentloaded", timeout=self._timeout
            )
            status_code = response.status if response else 0
            try:
                page.wait_for_load_state("networkidle", timeout=self.HYDRATION_WAIT_MS)
            except PlaywrightTimeout:
                # Tracking beacons keep the network busy — proceed with
                # whatever the DOM looks like right now.
                logger.info("networkidle timed out for %s; proceeding with DOM", url)
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
