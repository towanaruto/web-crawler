"""Test _persist_article — the boundary between parser output and DB+R2 writes."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from src.scheduler.job_manager import _persist_article
from src.storage.image_fetcher import FetchedImage


def _parsed(**overrides) -> dict:
    base = {
        "title": "Hello",
        "body_html": "<p>hi</p>",
        "body_text": "hi",
        "raw_html": "<html>hi</html>",
        "excerpt": "hi",
        "source_url": "https://example.com/a",
        "published_at": None,
        "featured_image_url": None,
        "category_names": [],
        "tag_names": [],
        "author_name": None,
        "word_count": 1,
        "links": [],
        "image_urls": [],
    }
    base.update(overrides)
    return base


class TestWithoutR2:
    def test_persists_without_raw_html_storage(self, db_session, auth_user):
        # Without R2 the raw HTML is discarded — the article is still saved.
        result = _persist_article(db_session, _parsed(), r2=None, user_id=auth_user.id)
        db_session.commit()

        assert result == 1
        from src.db.models import Article
        a = db_session.query(Article).one()
        assert a.raw_html_r2_key is None
        assert a.image_r2_keys == []

    def test_returns_zero_when_no_title(self, db_session, auth_user):
        result = _persist_article(
            db_session,
            _parsed(title=""),
            r2=None,
            user_id=auth_user.id,
        )
        assert result == 0


class TestWithR2:
    def test_uploads_raw_html_and_sets_key(self, db_session, auth_user):
        r2 = MagicMock()
        r2.put_raw_html.return_value = "articles/xx/raw.html"

        result = _persist_article(db_session, _parsed(), r2=r2, user_id=auth_user.id)
        db_session.commit()

        assert result == 1
        from src.db.models import Article
        a = db_session.query(Article).one()
        assert a.raw_html_r2_key == "articles/xx/raw.html"
        r2.put_raw_html.assert_called_once_with(a.id, "<html>hi</html>")

    def test_downloads_and_uploads_each_image(self, db_session, monkeypatch, auth_user):
        r2 = MagicMock()
        r2.put_raw_html.return_value = "articles/xx/raw.html"
        r2.put_image.side_effect = lambda art_id, idx, content, ct: f"articles/{art_id}/img-{idx:02d}.jpg"

        # Stub fetch_image at the import site used by job_manager.
        from src.scheduler import job_manager as jm
        monkeypatch.setattr(
            jm, "fetch_image",
            lambda url, **kw: FetchedImage(content=b"bytes-of-" + url.encode(), content_type="image/jpeg"),
        )

        parsed = _parsed(image_urls=["https://example.com/a.jpg", "https://example.com/b.jpg"])
        result = _persist_article(db_session, parsed, r2=r2, user_id=auth_user.id)
        db_session.commit()

        assert result == 1
        from src.db.models import Article
        a = db_session.query(Article).one()
        assert a.image_r2_keys == [
            f"articles/{a.id}/img-00.jpg",
            f"articles/{a.id}/img-01.jpg",
        ]
        assert r2.put_image.call_count == 2

    def test_skips_failed_image_downloads(self, db_session, monkeypatch, auth_user):
        r2 = MagicMock()
        r2.put_raw_html.return_value = "k"
        r2.put_image.side_effect = lambda art_id, idx, c, ct: f"img-{idx}"

        from src.scheduler import job_manager as jm
        # First URL succeeds, second returns None (e.g., 404 or non-image).
        results = [FetchedImage(b"x", "image/png"), None, FetchedImage(b"y", "image/png")]
        monkeypatch.setattr(jm, "fetch_image", lambda url, **kw: results.pop(0))

        parsed = _parsed(image_urls=["a", "b", "c"])
        _persist_article(db_session, parsed, r2=r2, user_id=auth_user.id)
        db_session.commit()

        from src.db.models import Article
        a = db_session.query(Article).one()
        # 2 successes (idx 0 and 2) — note that we use enumerate over the original
        # list, so the surviving keys match the *successful* indices.
        assert a.image_r2_keys == ["img-0", "img-2"]
