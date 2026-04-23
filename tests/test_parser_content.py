"""TDD tests driving Fix A (script/style/noscript/comment/JSON-LD removal)
and Fix B (text/image separation, trailing image list).
"""
from __future__ import annotations

import pytest

from src.parser.html_parser import parse_article


HTML_WITH_NOISE = """\
<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="Article">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"NewsArticle"}
  </script>
</head>
<body>
  <article>
    <script type="application/ld+json">
    {"inner":"payload"}
    </script>
    <style>.x{color:red}</style>
    <!-- tracking pixel -->
    <p>Paragraph one.</p>
    <img src="/a.jpg" alt="a">
    <p>Paragraph two with <img src="/inline.jpg" alt="inline"> image.</p>
    <img data-src="/b.jpg" alt="b">
    <img srcset="/small.jpg 400w, /large.jpg 1200w" alt="c">
    <img data-original="/d.jpg" alt="d">
    <noscript>Enable JS.</noscript>
  </article>
</body>
</html>
"""

BASE = "https://example.com/posts/1"


@pytest.fixture
def parsed():
    return parse_article(HTML_WITH_NOISE, BASE)


# ── Fix A: noise removal ──────────────────────────────────────────

class TestFixA_NoiseRemoval:
    def test_body_html_has_no_json_ld(self, parsed):
        assert "schema.org" not in parsed["body_html"]
        assert "@context" not in parsed["body_html"]
        assert "NewsArticle" not in parsed["body_html"]
        assert "payload" not in parsed["body_html"]

    def test_body_html_has_no_style_text(self, parsed):
        assert "color:red" not in parsed["body_html"]

    def test_body_html_has_no_noscript_text(self, parsed):
        assert "Enable JS" not in parsed["body_html"]

    def test_body_html_has_no_html_comment(self, parsed):
        assert "tracking pixel" not in parsed["body_html"]

    def test_body_text_has_no_json_ld(self, parsed):
        assert "schema.org" not in parsed["body_text"]
        assert "@context" not in parsed["body_text"]

    def test_body_text_has_no_noscript(self, parsed):
        assert "Enable JS" not in parsed["body_text"]

    def test_body_text_preserves_paragraphs(self, parsed):
        assert "Paragraph one" in parsed["body_text"]
        assert "Paragraph two" in parsed["body_text"]


# ── Fix B: text / image separation ────────────────────────────────

class TestFixB_ImageList:
    def test_body_html_contains_no_inline_img_in_prose(self, parsed):
        # All <img> must move to the trailing list, none remain inside <p>.
        prose, _, tail = parsed["body_html"].partition("<ul>")
        assert "<img" not in prose, f"inline <img> left in prose: {prose!r}"

    def test_body_html_ends_with_image_list(self, parsed):
        assert "<ul>" in parsed["body_html"]
        # Must be at the tail — last occurrence of <ul> should be near the end.
        assert parsed["body_html"].rstrip().endswith("</ul>")

    def test_image_list_has_li_img_structure(self, parsed):
        assert "<li><img" in parsed["body_html"]

    def test_image_urls_are_absolute(self, parsed):
        assert "https://example.com/a.jpg" in parsed["body_html"]
        assert "https://example.com/b.jpg" in parsed["body_html"]  # data-src
        assert "https://example.com/d.jpg" in parsed["body_html"]  # data-original
        # No bare relative path should remain in the image list.
        assert 'src="/a.jpg"' not in parsed["body_html"]

    def test_srcset_picks_largest_candidate(self, parsed):
        # srcset="/small.jpg 400w, /large.jpg 1200w" → pick large.jpg.
        assert "https://example.com/large.jpg" in parsed["body_html"]
        # small.jpg should not appear (we only take the highest-resolution URL).
        assert "small.jpg" not in parsed["body_html"]

    def test_inline_img_text_is_preserved(self, parsed):
        # The <p> that contained an inline <img> should still render its text.
        assert "Paragraph two with" in parsed["body_text"]
        assert "image." in parsed["body_text"]

    def test_image_list_deduplicates(self, parsed):
        # "/a.jpg" appears once in the source; should appear once in the list.
        assert parsed["body_html"].count("https://example.com/a.jpg") == 1


class TestCanonicalization:
    def test_source_url_canonicalized(self):
        html = "<html><head><title>x</title></head><body><article><p>x</p></article></body></html>"
        result = parse_article(html, "https://EXAMPLE.com/p?utm_source=tw#frag")
        assert result["source_url"] == "https://example.com/p"

    def test_link_canonical_tag_wins(self):
        html = """
        <html><head>
          <link rel="canonical" href="https://example.com/canonical-url">
        </head><body><article><p>x</p></article></body></html>
        """
        result = parse_article(html, "https://example.com/p?utm_source=tw")
        assert result["source_url"] == "https://example.com/canonical-url"

    def test_extracted_links_canonicalized(self):
        html = """
        <html><body><article>
          <p>x</p>
          <a href="/b?utm_source=tw&id=1">b</a>
        </article></body></html>
        """
        result = parse_article(html, "https://example.com/a")
        assert "https://example.com/b?id=1" in result["links"]
