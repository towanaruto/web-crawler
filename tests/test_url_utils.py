from src.parser.url_utils import canonicalize_url


class TestCanonicalizeUrl:
    def test_lowercases_scheme_and_host(self):
        assert canonicalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"

    def test_strips_fragment(self):
        assert canonicalize_url("https://a.com/x#section") == "https://a.com/x"

    def test_strips_default_ports(self):
        assert canonicalize_url("https://a.com:443/x") == "https://a.com/x"
        assert canonicalize_url("http://a.com:80/x") == "http://a.com/x"

    def test_keeps_non_default_port(self):
        assert canonicalize_url("https://a.com:8443/x") == "https://a.com:8443/x"

    def test_removes_utm_parameters(self):
        assert (
            canonicalize_url("https://a.com/p?utm_source=x&utm_medium=y&id=1")
            == "https://a.com/p?id=1"
        )

    def test_removes_facebook_tracking(self):
        assert canonicalize_url("https://a.com/p?fbclid=abc") == "https://a.com/p"

    def test_removes_google_tracking(self):
        assert canonicalize_url("https://a.com/p?gclid=abc&q=real") == "https://a.com/p?q=real"

    def test_sorts_query_params(self):
        assert canonicalize_url("https://a.com/p?b=2&a=1") == "https://a.com/p?a=1&b=2"

    def test_preserves_meaningful_params(self):
        # lang / page / id must survive.
        assert canonicalize_url("https://a.com/p?lang=ja&page=2") == "https://a.com/p?lang=ja&page=2"

    def test_handles_empty_query(self):
        assert canonicalize_url("https://a.com/p?") == "https://a.com/p"

    def test_preserves_trailing_slash(self):
        # Do not fold /p/ and /p to the same URL — different routers treat
        # them differently; we stay conservative.
        assert canonicalize_url("https://a.com/p/") == "https://a.com/p/"
        assert canonicalize_url("https://a.com/p") == "https://a.com/p"

    def test_unicode_host_lowercased(self):
        assert canonicalize_url("https://Example.JP/x") == "https://example.jp/x"
