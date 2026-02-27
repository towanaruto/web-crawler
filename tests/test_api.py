from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.engine import get_db


def override_get_db():
    """Override DB dependency with mock."""
    db = MagicMock()
    yield db


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestArticlesEndpoint:
    @patch("src.api.routes.articles.list_articles")
    def test_list_articles(self, mock_list):
        mock_article = MagicMock()
        mock_article.id = uuid4()
        mock_article.title = "Test"
        mock_article.slug = "test"
        mock_article.excerpt = "excerpt"
        mock_article.source_url = "https://example.com"
        mock_article.author = None
        mock_article.category = None
        mock_article.tags = []
        mock_article.published_at = None
        mock_article.featured_image_url = None
        mock_article.word_count = 100
        mock_article.status = "draft"

        mock_list.return_value = ([mock_article], 1)

        response = client.get("/api/articles")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test"

    @patch("src.api.routes.articles.get_article_by_slug")
    def test_get_article_not_found(self, mock_get):
        mock_get.return_value = None
        response = client.get("/api/articles/nonexistent")
        assert response.status_code == 404


class TestCategoriesEndpoint:
    @patch("src.api.routes.categories.list_categories")
    def test_list_categories(self, mock_list):
        mock_cat = MagicMock()
        mock_cat.id = uuid4()
        mock_cat.name = "Tech"
        mock_cat.slug = "tech"
        mock_list.return_value = [mock_cat]

        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Tech"
