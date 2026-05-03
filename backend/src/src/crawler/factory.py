from __future__ import annotations

from src.crawler.base import BaseCrawler
from src.crawler.static_crawler import StaticCrawler
from src.crawler.dynamic_crawler import DynamicCrawler


def create_crawler(mode: str = "static") -> BaseCrawler:
    """Factory function to create the appropriate crawler."""
    if mode == "dynamic":
        return DynamicCrawler()
    return StaticCrawler()
