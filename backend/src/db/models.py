import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    slug = Column(String(256), unique=True, nullable=False)
    source_url = Column(Text)
    bio = Column(Text)

    articles = relationship("Article", back_populates="author")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    slug = Column(String(256), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side="Category.id", backref="children")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False)
    slug = Column(String(128), unique=True, nullable=False)


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id = Column(
        UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(512), nullable=False)
    slug = Column(String(512), unique=True, nullable=False)
    body_text = Column(Text)
    body_html = Column(Text)
    raw_html = Column(Text)
    excerpt = Column(String(1000))
    source_url = Column(Text, unique=True, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    published_at = Column(DateTime(timezone=True))
    crawled_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status = Column(String(20), default="draft")
    featured_image_url = Column(Text)
    word_count = Column(Integer)

    author = relationship("Author", back_populates="articles")
    category = relationship("Category")
    tags = relationship("Tag", secondary="article_tags", backref="articles")

    __table_args__ = (
        Index("ix_articles_published_at", published_at.desc()),
        Index("ix_articles_source_url", "source_url", unique=True),
        Index("ix_articles_slug", "slug", unique=True),
    )


class CrawlTarget(Base):
    __tablename__ = "crawl_targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_url = Column(Text, unique=True, nullable=False)
    crawl_mode = Column(String(20), nullable=False, default="static")
    selector_config = Column(JSONB, default=dict)
    max_depth = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)

    jobs = relationship("CrawlJob", back_populates="target")


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(
        UUID(as_uuid=True), ForeignKey("crawl_targets.id"), nullable=False
    )
    target_url = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    http_status_code = Column(Integer)
    error_message = Column(Text)
    articles_found = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))

    target = relationship("CrawlTarget", back_populates="jobs")
