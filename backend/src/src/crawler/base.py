from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CrawlResult:
    url: str
    status_code: int
    html: str
    error: str | None = None


class BaseCrawler(ABC):
    """Abstract base class for all crawlers."""

    USER_AGENT = "WebCrawlerBot/1.0"

    @abstractmethod
    def fetch(self, url: str) -> CrawlResult:
        """Fetch a URL and return its HTML content."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Clean up any resources."""
        ...

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
