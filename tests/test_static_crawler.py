from unittest.mock import MagicMock, patch

from src.crawler.static_crawler import StaticCrawler


class TestStaticCrawler:
    def test_fetch_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Hello</body></html>"

        with patch("src.crawler.static_crawler.requests.Session") as MockSession:
            instance = MockSession.return_value
            instance.get.return_value = mock_response

            crawler = StaticCrawler()
            result = crawler.fetch("https://example.com")

            assert result.status_code == 200
            assert "Hello" in result.html
            assert result.error is None
            crawler.close()

    def test_fetch_error(self):
        import requests

        with patch("src.crawler.static_crawler.requests.Session") as MockSession:
            instance = MockSession.return_value
            instance.get.side_effect = requests.RequestException("Connection error")

            crawler = StaticCrawler()
            result = crawler.fetch("https://example.com")

            assert result.status_code == 0
            assert result.error == "Connection error"
            crawler.close()

    def test_context_manager(self):
        with patch("src.crawler.static_crawler.requests.Session"):
            with StaticCrawler() as crawler:
                assert crawler is not None
