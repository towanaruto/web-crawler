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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(256), nullable=False)
    slug = Column(String(256), unique=True, nullable=False)
    source_url = Column(Text)
    bio = Column(Text)

    articles = relationship("Article", back_populates="author")


class Category(Base):
    __tablename__ = "categories"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(256), nullable=False)
    slug = Column(String(256), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side="Category.id", backref="children")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(128), nullable=False)
    slug = Column(String(128), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    auth0_sub = Column(String(255), unique=True, nullable=False)
    email = Column(String(320), nullable=False)
    name = Column(String(256), nullable=True)
    picture_url = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    articles = relationship("Article", back_populates="user")
    crawl_targets = relationship("CrawlTarget", back_populates="user")
    crawl_jobs = relationship("CrawlJob", back_populates="user")

    __table_args__ = (Index("ix_users_email", "email"),)


class Invite(Base):
    __tablename__ = "invites"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email = Column(String(320), nullable=False)
    code_hash = Column(String(128), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    used_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    used_by_auth0_sub = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    used_by_user = relationship("User")

    __table_args__ = (Index("ix_invites_email", "email"),)


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

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(512), nullable=False)
    slug = Column(String(512), nullable=False)
    body_text = Column(Text)
    body_html = Column(Text)
    raw_html_r2_key = Column(String(255), nullable=True)
    image_r2_keys = Column(JSONB, default=list, nullable=False)
    excerpt = Column(String(1000))
    source_url = Column(Text, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    published_at = Column(DateTime(timezone=True))
    crawled_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status = Column(String(20), default="draft")
    featured_image_url = Column(Text)
    word_count = Column(Integer)

    user = relationship("User", back_populates="articles")
    author = relationship("Author", back_populates="articles")
    category = relationship("Category")
    tags = relationship("Tag", secondary="article_tags", backref="articles")

    __table_args__ = (
        UniqueConstraint("user_id", "source_url", name="uq_articles_user_source_url"),
        UniqueConstraint("user_id", "slug", name="uq_articles_user_slug"),
        Index("ix_articles_published_at", published_at.desc()),
        Index("ix_articles_user_crawled_at", "user_id", crawled_at.desc()),
    )


class CrawlTarget(Base):
    __tablename__ = "crawl_targets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    base_url = Column(Text, nullable=False)
    crawl_mode = Column(String(20), nullable=False, default="static")
    selector_config = Column(JSONB, default=dict)
    max_depth = Column(Integer, default=2)
    is_active = Column(Boolean, default=True)
    keywords = Column(JSONB, default=list)
    keyword_mode = Column(String(10), default="any")
    schedule_enabled = Column(Boolean, default=False, nullable=False)
    schedule_config = Column(JSONB, default=dict)
    schedule_timezone = Column(String(64), default="Asia/Tokyo", nullable=False)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    last_scheduled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="crawl_targets")
    jobs = relationship("CrawlJob", back_populates="target")

    __table_args__ = (
        UniqueConstraint("user_id", "base_url", name="uq_crawl_targets_user_base_url"),
        Index("ix_crawl_targets_user_active", "user_id", "is_active"),
        Index("ix_crawl_targets_schedule_due", "schedule_enabled", "next_run_at"),
    )


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
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

    user = relationship("User", back_populates="crawl_jobs")
    target = relationship("CrawlTarget", back_populates="jobs")

    __table_args__ = (Index("ix_crawl_jobs_user_started_at", "user_id", started_at.desc()),)
