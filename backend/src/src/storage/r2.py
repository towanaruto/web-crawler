"""Cloudflare R2 storage adapter (S3-compatible).

R2 exposes an S3-compatible API at
``https://<account_id>.r2.cloudflarestorage.com``. boto3 talks to it with the
standard ``s3`` client and ``region_name="auto"``. Object reads can be served
from the bucket's public URL (``R2_PUBLIC_URL``) when the bucket is configured
for public access; otherwise the caller can sign URLs separately.
"""
from __future__ import annotations

import uuid
from typing import Optional

import boto3
from botocore.client import Config


_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/avif": "avif",
    "image/svg+xml": "svg",
}


class R2Storage:
    """Thin wrapper around boto3 for R2 reads/writes.

    The class is constructed with an explicit boto3 client (or builds one from
    explicit credentials). Tests inject a stubbed client; production callers
    use :func:`build_r2_storage_from_settings`.
    """

    def __init__(self, *, client, bucket: str, public_url: str):
        self._client = client
        self._bucket = bucket
        self._public_url = public_url.rstrip("/")

    def put_raw_html(self, article_id: uuid.UUID, html: str) -> str:
        key = f"articles/{article_id}/raw.html"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=html.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )
        return key

    def put_image(
        self,
        article_id: uuid.UUID,
        idx: int,
        content: bytes,
        content_type: str,
    ) -> str:
        ext = _EXT_BY_CONTENT_TYPE.get(content_type.lower(), "bin")
        key = f"articles/{article_id}/img-{idx:02d}.{ext}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return key

    def public_url(self, key: str) -> str:
        return f"{self._public_url}/{key}"


def build_r2_client(
    account_id: str,
    access_key_id: str,
    secret_access_key: str,
):
    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def build_r2_storage_from_settings(settings) -> Optional[R2Storage]:
    """Construct an R2Storage from the global Settings object.

    Returns None when any required env var is missing — callers should fall
    back to a no-op (skip R2 uploads) so local development without R2 keys
    keeps working.
    """
    required = (
        settings.R2_ACCOUNT_ID,
        settings.R2_ACCESS_KEY_ID,
        settings.R2_SECRET_ACCESS_KEY,
        settings.R2_BUCKET,
        settings.R2_PUBLIC_URL,
    )
    if not all(required):
        return None
    client = build_r2_client(
        settings.R2_ACCOUNT_ID,
        settings.R2_ACCESS_KEY_ID,
        settings.R2_SECRET_ACCESS_KEY,
    )
    return R2Storage(
        client=client,
        bucket=settings.R2_BUCKET,
        public_url=settings.R2_PUBLIC_URL,
    )
