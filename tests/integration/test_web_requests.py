import pytest
import responses
from tests.test_data.mock_html_responses import MOCK_IN_STOCK_HTML

def test_real_website_request(sample_stock_checker):
    """Test requesting HTML from a real website"""
    url = "https://www.example.com"  # Use a reliable test website
    html = sample_stock_checker.get_html_from_url(url)
    assert html is not None
    assert len(html) > 0

@responses.activate
def test_mocked_web_request(sample_stock_checker):
    """Test web request with mocked response"""
    test_url = "https://test.example.com/product"
    responses.add(
        responses.GET,
        test_url,
        body=MOCK_IN_STOCK_HTML,
        status=200
    )
    
    html = sample_stock_checker.get_html_from_url(test_url)
    assert html == MOCK_IN_STOCK_HTML