"""Tests for R2Storage. Uses botocore.stub.Stubber so no real R2 calls fire."""
from __future__ import annotations

import uuid

import boto3
import pytest
from botocore.client import Config
from botocore.stub import Stubber

from src.storage.r2 import R2Storage, build_r2_storage_from_settings


@pytest.fixture
def stub_client():
    client = boto3.client(
        "s3",
        endpoint_url="https://acc.r2.cloudflarestorage.com",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    stubber = Stubber(client)
    stubber.activate()
    yield client, stubber
    stubber.deactivate()


@pytest.fixture
def storage(stub_client):
    client, _ = stub_client
    return R2Storage(client=client, bucket="my-bucket", public_url="https://pub.example.com/")


class TestPutRawHtml:
    def test_returns_expected_key(self, stub_client, storage):
        client, stubber = stub_client
        article_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
        stubber.add_response(
            "put_object",
            {},
            expected_params={
                "Bucket": "my-bucket",
                "Key": f"articles/{article_id}/raw.html",
                "Body": b"<html>hi</html>",
                "ContentType": "text/html; charset=utf-8",
            },
        )

        key = storage.put_raw_html(article_id, "<html>hi</html>")

        assert key == f"articles/{article_id}/raw.html"
        stubber.assert_no_pending_responses()

    def test_unicode_html_encoded_utf8(self, stub_client, storage):
        client, stubber = stub_client
        article_id = uuid.uuid4()
        stubber.add_response(
            "put_object",
            {},
            expected_params={
                "Bucket": "my-bucket",
                "Key": f"articles/{article_id}/raw.html",
                "Body": "<p>日本語</p>".encode("utf-8"),
                "ContentType": "text/html; charset=utf-8",
            },
        )

        storage.put_raw_html(article_id, "<p>日本語</p>")
        stubber.assert_no_pending_responses()


class TestPutImage:
    @pytest.mark.parametrize(
        "content_type,expected_ext",
        [
            ("image/jpeg", "jpg"),
            ("image/JPG", "jpg"),  # case-insensitive
            ("image/png", "png"),
            ("image/webp", "webp"),
            ("image/gif", "gif"),
            ("image/avif", "avif"),
            ("image/svg+xml", "svg"),
            ("application/octet-stream", "bin"),  # fallback
        ],
    )
    def test_extension_mapping(self, stub_client, storage, content_type, expected_ext):
        client, stubber = stub_client
        article_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        idx = 3
        body = b"\x89PNGfake"
        stubber.add_response(
            "put_object",
            {},
            expected_params={
                "Bucket": "my-bucket",
                "Key": f"articles/{article_id}/img-03.{expected_ext}",
                "Body": body,
                "ContentType": content_type,
            },
        )

        key = storage.put_image(article_id, idx, body, content_type)

        assert key == f"articles/{article_id}/img-03.{expected_ext}"
        stubber.assert_no_pending_responses()

    def test_index_is_zero_padded(self, stub_client, storage):
        client, stubber = stub_client
        article_id = uuid.uuid4()
        stubber.add_response(
            "put_object",
            {},
            expected_params={
                "Bucket": "my-bucket",
                "Key": f"articles/{article_id}/img-00.jpg",
                "Body": b"x",
                "ContentType": "image/jpeg",
            },
        )
        key = storage.put_image(article_id, 0, b"x", "image/jpeg")
        assert key.endswith("img-00.jpg")


class TestPublicUrl:
    def test_joins_with_public_base(self, storage):
        assert (
            storage.public_url("articles/abc/raw.html")
            == "https://pub.example.com/articles/abc/raw.html"
        )

    def test_strips_trailing_slash_from_base(self, stub_client):
        client, _ = stub_client
        s = R2Storage(client=client, bucket="b", public_url="https://x.com///")
        assert s.public_url("a/b") == "https://x.com/a/b"


class TestBuildFromSettings:
    def test_returns_none_when_any_missing(self):
        class S:
            R2_ACCOUNT_ID = "acc"
            R2_ACCESS_KEY_ID = "key"
            R2_SECRET_ACCESS_KEY = "secret"
            R2_BUCKET = "bucket"
            R2_PUBLIC_URL = None  # missing

        assert build_r2_storage_from_settings(S()) is None

    def test_returns_storage_when_all_present(self):
        class S:
            R2_ACCOUNT_ID = "acc"
            R2_ACCESS_KEY_ID = "key"
            R2_SECRET_ACCESS_KEY = "secret"
            R2_BUCKET = "bucket"
            R2_PUBLIC_URL = "https://pub.com"

        s = build_r2_storage_from_settings(S())
        assert isinstance(s, R2Storage)
