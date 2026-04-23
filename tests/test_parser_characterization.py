"""Characterization tests for html_parser.

Two kinds of assertions live here:

1. Regression guards — behaviour we want preserved through the Fix A / Fix B
   refactor (title, og:image, author, published_at, links, excerpt).
2. Current-state pins — document the *current* (buggy) output so that Fix A / B
   flipping them is explicit and reviewable. These are marked with ``CURRENT:``
   in the assertion message and will be updated during Fix A / Fix B.
"""
from __future__ import annotations

import pytest

from src.parser.html_parser import parse_article


SAMPLE_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <title>News Site</title>
  <meta property="og:title" content="Breaking News Today">
  <meta property="og:image" content="https://example.com/hero.jpg">
  <meta name="description" content="A summary of breaking news for testing.">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"NewsArticle","headline":"Breaking","author":"Jane Smith"}
  </script>
  <script>window.__tracking = {user: "alice"};</script>
  <style>.hidden{display:none;}</style>
</head>
<body>
  <h1>Breaking News Today</h1>
  <span class="author">Jane Smith</span>
  <time datetime="2026-04-22T09:00:00+00:00">April 22, 2026</time>
  <span class="category">World</span>
  <article>
    <!-- advertisement block start -->
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"NewsArticle","headline":"Breaking"}
    </script>
    <style>.inline-ad{display:block}</style>
    <p>The first paragraph of the story.</p>
    <img src="/images/photo1.jpg" alt="Photo 1">
    <p>The second paragraph continues the story.</p>
    <img data-src="/images/photo2.jpg" alt="Photo 2">
    <p>한국어 と 日本語 が混じった段落。</p>
    <img srcset="/images/small.jpg 400w, /images/large.jpg 1200w" alt="Photo 3">
    <noscript>JavaScript is required to view this site.</noscript>
    <a href="/related">Related story</a>
  </article>
</body>
</html>
"""

BASE_URL = "https://example.com/articles/breaking"


@pytest.fixture
def parsed():
    return parse_article(SAMPLE_HTML, BASE_URL)


# ── Regression guards ─────────────────────────────────────────────

class TestRegressionGuards:
    def test_title_extracted(self, parsed):
        assert parsed["title"] == "Breaking News Today"

    def test_og_image_extracted(self, parsed):
        assert parsed["featured_image_url"] == "https://example.com/hero.jpg"

    def test_author_extracted(self, parsed):
        assert parsed["author_name"] == "Jane Smith"

    def test_published_at_extracted(self, parsed):
        assert parsed["published_at"] is not None
        assert parsed["published_at"].year == 2026
        assert parsed["published_at"].month == 4

    def test_excerpt_extracted(self, parsed):
        assert "breaking news" in parsed["excerpt"].lower()

    def test_links_extracted(self, parsed):
        assert "https://example.com/related" in parsed["links"]

    def test_category_extracted(self, parsed):
        assert "World" in parsed["category_names"]

    def test_multilingual_text_preserved(self, parsed):
        # Regression: non-ASCII text must survive parsing unchanged.
        assert "한국어" in parsed["body_text"]
        assert "日本語" in parsed["body_text"]


# ── Current-state pins (will flip during Fix A / Fix B) ───────────

class TestCurrentState:
    """Document the current (pre-fix) behaviour of the parser.

    These assertions will be updated (flipped) once Fix A / Fix B land.
    """

    def test_body_html_has_no_json_ld_payload(self, parsed):
        # Flipped after Fix A: JSON-LD payload must be removed before bleach.
        assert "schema.org" not in parsed["body_html"]
        assert "NewsArticle" not in parsed["body_html"]

    def test_body_html_has_no_style_content(self, parsed):
        # Flipped after Fix A: <style> text is gone.
        assert "display:block" not in parsed["body_html"]
        assert "inline-ad" not in parsed["body_html"]

    def test_body_html_has_no_inline_img_in_prose(self, parsed):
        # Flipped after Fix B: inline <img> moved to trailing <ul>.
        prose, _, _ = parsed["body_html"].partition("<ul>")
        assert "<img" not in prose

    def test_body_html_ends_with_image_list(self, parsed):
        # Flipped after Fix B: trailing <ul><li><img></li></ul> present.
        assert parsed["body_html"].rstrip().endswith("</ul>")
