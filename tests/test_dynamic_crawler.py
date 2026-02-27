from unittest.mock import MagicMock, patch


class TestDynamicCrawler:
    @patch("src.crawler.dynamic_crawler.sync_playwright")
    def test_fetch_success(self, mock_pw_func):
        mock_pw = MagicMock()
        mock_pw_func.return_value.start.return_value = mock_pw

        mock_browser = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_page.content.return_value = "<html><body>SPA Content</body></html>"

        from src.crawler.dynamic_crawler import DynamicCrawler

        crawler = DynamicCrawler()
        result = crawler.fetch("https://spa-example.com")

        assert result.status_code == 200
        assert "SPA Content" in result.html
        assert result.error is None
        crawler.close()

    @patch("src.crawler.dynamic_crawler.sync_playwright")
    def test_fetch_error(self, mock_pw_func):
        mock_pw = MagicMock()
        mock_pw_func.return_value.start.return_value = mock_pw

        mock_browser = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_page.goto.side_effect = Exception("Timeout")

        from src.crawler.dynamic_crawler import DynamicCrawler

        crawler = DynamicCrawler()
        result = crawler.fetch("https://spa-example.com")

        assert result.status_code == 0
        assert result.error == "Timeout"
        crawler.close()
