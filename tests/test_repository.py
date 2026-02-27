import uuid

import pytest

from src.db.repository import (
    get_article_by_slug,
    get_or_create_author,
    get_or_create_category,
    get_or_create_tag,
    list_articles,
    upsert_article,
)


class TestRepository:
    def test_upsert_article_insert(self, db_session):
        data = {
            "title": "Test Article",
            "slug": "test-article",
            "source_url": "https://example.com/test",
            "body_text": "Test body",
        }
        article = upsert_article(db_session, data)
        db_session.commit()

        assert article.title == "Test Article"
        assert article.slug == "test-article"

    def test_upsert_article_update(self, db_session):
        data = {
            "title": "Original",
            "slug": "original",
            "source_url": "https://example.com/original",
        }
        upsert_article(db_session, data)
        db_session.commit()

        updated = upsert_article(db_session, {
            "title": "Updated",
            "source_url": "https://example.com/original",
        })
        db_session.commit()

        assert updated.title == "Updated"

    def test_upsert_article_slug_uniqueness(self, db_session):
        upsert_article(db_session, {
            "title": "Same Title",
            "slug": "same-title",
            "source_url": "https://example.com/1",
        })
        db_session.commit()

        article2 = upsert_article(db_session, {
            "title": "Same Title",
            "slug": "same-title",
            "source_url": "https://example.com/2",
        })
        db_session.commit()

        assert article2.slug == "same-title-1"

    def test_get_article_by_slug(self, db_session):
        upsert_article(db_session, {
            "title": "Find Me",
            "slug": "find-me",
            "source_url": "https://example.com/find",
        })
        db_session.commit()

        found = get_article_by_slug(db_session, "find-me")
        assert found is not None
        assert found.title == "Find Me"

        not_found = get_article_by_slug(db_session, "nope")
        assert not_found is None

    def test_list_articles(self, db_session):
        for i in range(5):
            upsert_article(db_session, {
                "title": f"Article {i}",
                "slug": f"article-{i}",
                "source_url": f"https://example.com/{i}",
            })
        db_session.commit()

        articles, total = list_articles(db_session, limit=3)
        assert len(articles) == 3
        assert total == 5

    def test_get_or_create_category(self, db_session):
        cat1 = get_or_create_category(db_session, "Technology")
        cat2 = get_or_create_category(db_session, "Technology")
        assert cat1.id == cat2.id
        assert cat1.slug == "technology"

    def test_get_or_create_author(self, db_session):
        author1 = get_or_create_author(db_session, "John Doe")
        author2 = get_or_create_author(db_session, "John Doe")
        assert author1.id == author2.id

    def test_get_or_create_tag(self, db_session):
        tag1 = get_or_create_tag(db_session, "Python")
        tag2 = get_or_create_tag(db_session, "Python")
        assert tag1.id == tag2.id
        assert tag1.slug == "python"
