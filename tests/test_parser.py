from src.parser.html_parser import parse_article


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Test Article">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta name="description" content="A test article about testing">
</head>
<body>
    <h1>Test Article Title</h1>
    <span class="author">John Doe</span>
    <time datetime="2025-01-15T10:00:00+00:00">January 15, 2025</time>
    <span class="category">Technology</span>
    <span class="tag">Python</span>
    <span class="tag">Testing</span>
    <article>
        <p>This is the body of the test article.</p>
        <p>It has multiple paragraphs for testing purposes.</p>
        <a href="/another-page">Link to another page</a>
    </article>
</body>
</html>
"""


class TestParser:
    def test_parse_title(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert result["title"] == "Test Article Title"

    def test_parse_body(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert "test article" in result["body_text"].lower()
        assert result["word_count"] > 0

    def test_parse_author(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert result["author_name"] == "John Doe"

    def test_parse_datetime(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert result["published_at"] is not None
        assert result["published_at"].year == 2025

    def test_parse_featured_image(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert result["featured_image_url"] == "https://example.com/image.jpg"

    def test_parse_excerpt(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert result["excerpt"] == "A test article about testing"

    def test_parse_tags(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert "Python" in result["tag_names"]
        assert "Testing" in result["tag_names"]

    def test_parse_categories(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert "Technology" in result["category_names"]

    def test_parse_links(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert "https://example.com/another-page" in result["links"]

    def test_source_url_preserved(self):
        result = parse_article(SAMPLE_HTML, "https://example.com/article")
        assert result["source_url"] == "https://example.com/article"
