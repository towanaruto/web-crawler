"""Download images from arbitrary URLs to R2-bound bytes.

Separated from R2Storage because the responsibilities are different: this
module pulls bytes from the public internet, R2Storage pushes bytes to R2.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15.0
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB
USER_AGENT = "WebCrawlerBot/1.0"


@dataclass(frozen=True)
class FetchedImage:
    content: bytes
    content_type: str


class ImageTooLarge(Exception):
    pass


def fetch_image(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    session: requests.Session | None = None,
) -> FetchedImage | None:
    """Fetch an image URL into memory.

    Returns None on any failure (timeout, non-2xx, non-image content type).
    Raises ImageTooLarge when the response body exceeds ``max_bytes`` so the
    caller can record the failure rather than silently truncating.
    """
    sess = session or requests
    try:
        resp = sess.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            stream=True,
        )
    except requests.RequestException as e:
        logger.warning("fetch_image request failed for %s: %s", url, e)
        return None

    if resp.status_code != 200:
        logger.info("fetch_image %s returned %d", url, resp.status_code)
        resp.close()
        return None

    content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        logger.info("fetch_image %s skipped: content-type=%s", url, content_type)
        resp.close()
        return None

    chunks: list[bytes] = []
    total = 0
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            resp.close()
            raise ImageTooLarge(f"{url} exceeded {max_bytes} bytes")
        chunks.append(chunk)
    resp.close()

    return FetchedImage(content=b"".join(chunks), content_type=content_type)
