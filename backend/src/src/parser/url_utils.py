"""URL canonicalization for deduplication.

Implemented with stdlib only (no w3lib dependency). The strategy is
conservative: lowercase scheme/host, drop default ports and fragments,
remove well-known tracking query parameters, sort remaining query keys.
Trailing-slash policy is *preserved* (not folded) because many routers
distinguish /p/ from /p.
"""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS: frozenset[str] = frozenset(
    {
        # Google / GA
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "utm_id", "utm_name", "gclid", "gclsrc", "dclid",
        # Facebook / Meta
        "fbclid",
        # Mailchimp
        "mc_eid", "mc_cid",
        # HubSpot
        "_hsenc", "_hsmi", "hsctatracking",
        # Instagram / TikTok
        "igshid", "ttclid",
        # Yahoo / MS
        "yclid", "msclkid",
    }
)

_DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443}


def canonicalize_url(url: str) -> str:
    """Return a canonical form suitable for equality-based deduplication."""
    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    host = parts.hostname.lower() if parts.hostname else ""
    port = parts.port
    if port and _DEFAULT_PORTS.get(scheme) == port:
        port = None
    netloc = host
    if parts.username or parts.password:
        cred = parts.username or ""
        if parts.password:
            cred += f":{parts.password}"
        netloc = f"{cred}@{netloc}"
    if port:
        netloc = f"{netloc}:{port}"

    pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    pairs.sort(key=lambda kv: kv[0])
    query = urlencode(pairs, doseq=True)

    return urlunsplit((scheme, netloc, parts.path, query, ""))
