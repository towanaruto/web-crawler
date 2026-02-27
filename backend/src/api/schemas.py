from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class AuthorOut(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ArticleListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    excerpt: Optional[str]
    source_url: str
    author: Optional[AuthorOut]
    category: Optional[CategoryOut]
    tags: List[TagOut]
    published_at: Optional[datetime]
    featured_image_url: Optional[str]
    word_count: Optional[int]
    status: str

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleListItem):
    body_html: Optional[str]
    body_text: Optional[str]
    crawled_at: Optional[datetime]


class PaginatedArticles(BaseModel):
    items: List[ArticleListItem]
    total: int
    offset: int
    limit: int


class CrawlRequest(BaseModel):
    url: str
    mode: str = "static"


class CrawlResponse(BaseModel):
    targets_crawled: int
    articles_found: int
    failed: int


class HealthResponse(BaseModel):
    status: str
    db: str
