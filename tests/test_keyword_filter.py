from src.parser.keyword_filter import matches_keywords


def _make_parsed(
    title="Sample Article",
    body_text="",
    excerpt="",
    category_names=None,
    tag_names=None,
):
    return {
        "title": title,
        "body_text": body_text,
        "excerpt": excerpt,
        "category_names": category_names or [],
        "tag_names": tag_names or [],
    }


class TestEmptyKeywords:
    def test_empty_list_always_passes(self):
        assert matches_keywords(_make_parsed(), [], "any") is True

    def test_empty_list_all_mode_passes(self):
        assert matches_keywords(_make_parsed(), [], "all") is True


class TestAnyMode:
    def test_single_match_passes(self):
        parsed = _make_parsed(title="Introduction to Python programming")
        assert matches_keywords(parsed, ["python"], "any") is True

    def test_no_match_fails(self):
        parsed = _make_parsed(title="Introduction to Java programming")
        assert matches_keywords(parsed, ["python", "rust"], "any") is False

    def test_one_of_many_matches(self):
        parsed = _make_parsed(title="AI and Machine Learning")
        assert matches_keywords(parsed, ["python", "AI", "rust"], "any") is True


class TestAllMode:
    def test_all_match_passes(self):
        parsed = _make_parsed(title="Python AI tutorial")
        assert matches_keywords(parsed, ["python", "AI"], "all") is True

    def test_partial_match_fails(self):
        parsed = _make_parsed(title="Python tutorial")
        assert matches_keywords(parsed, ["python", "AI"], "all") is False


class TestCaseInsensitive:
    def test_uppercase_keyword(self):
        parsed = _make_parsed(title="python basics")
        assert matches_keywords(parsed, ["PYTHON"], "any") is True

    def test_mixed_case(self):
        parsed = _make_parsed(title="PyThOn Basics")
        assert matches_keywords(parsed, ["python"], "any") is True


class TestTagsAndCategories:
    def test_match_in_tags(self):
        parsed = _make_parsed(title="Some article", tag_names=["python", "web"])
        assert matches_keywords(parsed, ["python"], "any") is True

    def test_match_in_categories(self):
        parsed = _make_parsed(title="Some article", category_names=["Technology"])
        assert matches_keywords(parsed, ["technology"], "any") is True

    def test_no_match_anywhere(self):
        parsed = _make_parsed(
            title="Cooking tips",
            body_text="How to make pasta",
            tag_names=["food", "recipe"],
            category_names=["Lifestyle"],
        )
        assert matches_keywords(parsed, ["python"], "any") is False


class TestBodyAndExcerpt:
    def test_match_in_body(self):
        parsed = _make_parsed(title="Article", body_text="Learn about machine learning")
        assert matches_keywords(parsed, ["machine learning"], "any") is True

    def test_match_in_excerpt(self):
        parsed = _make_parsed(title="Article", excerpt="A deep dive into AI")
        assert matches_keywords(parsed, ["AI"], "any") is True
