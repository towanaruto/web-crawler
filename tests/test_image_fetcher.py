from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from src.storage.image_fetcher import (
    DEFAULT_MAX_BYTES,
    FetchedImage,
    ImageTooLarge,
    fetch_image,
)


def _make_response(*, status=200, content_type="image/jpeg", chunks=(b"",)):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.headers = {"Content-Type": content_type}
    resp.iter_content.return_value = iter(chunks)
    resp.close = MagicMock()
    return resp


def _session_returning(resp):
    s = MagicMock(spec=requests.Session)
    s.get.return_value = resp
    return s


class TestSuccessPath:
    def test_returns_fetched_image(self):
        resp = _make_response(content_type="image/png", chunks=(b"\x89PNG", b"data"))
        sess = _session_returning(resp)

        result = fetch_image("https://x.com/a.png", session=sess)

        assert isinstance(result, FetchedImage)
        assert result.content == b"\x89PNGdata"
        assert result.content_type == "image/png"

    def test_strips_charset_from_content_type(self):
        resp = _make_response(content_type="image/jpeg; charset=binary", chunks=(b"x",))
        sess = _session_returning(resp)
        result = fetch_image("https://x.com/a.jpg", session=sess)
        assert result.content_type == "image/jpeg"


class TestFailurePaths:
    def test_request_exception_returns_none(self):
        sess = MagicMock(spec=requests.Session)
        sess.get.side_effect = requests.Timeout("slow")
        assert fetch_image("https://x.com/a.jpg", session=sess) is None

    def test_non_200_returns_none(self):
        resp = _make_response(status=404)
        sess = _session_returning(resp)
        assert fetch_image("https://x.com/a.jpg", session=sess) is None

    def test_non_image_content_type_returns_none(self):
        resp = _make_response(content_type="text/html", chunks=(b"<html>",))
        sess = _session_returning(resp)
        assert fetch_image("https://x.com/a.jpg", session=sess) is None


class TestSizeLimit:
    def test_raises_image_too_large(self):
        big = b"x" * (DEFAULT_MAX_BYTES + 1)
        resp = _make_response(chunks=(big,))
        sess = _session_returning(resp)
        with pytest.raises(ImageTooLarge):
            fetch_image("https://x.com/a.jpg", session=sess)

    def test_respects_explicit_max_bytes(self):
        resp = _make_response(chunks=(b"abc", b"def"))
        sess = _session_returning(resp)
        with pytest.raises(ImageTooLarge):
            fetch_image("https://x.com/a.jpg", session=sess, max_bytes=4)
