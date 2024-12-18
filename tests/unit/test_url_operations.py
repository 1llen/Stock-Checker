import pytest

def test_get_html_from_url_invalid_url(sample_stock_checker):
    """Test fetching HTML from invalid URL"""
    result = sample_stock_checker.get_html_from_url("https://invalid.url.example")
    assert result is None

def test_url_stripping(sample_stock_checker, create_test_csv):
    """Test that URLs are properly stripped of quotes"""
    urls = sample_stock_checker.get_url_list("test_urls.csv", "elite_trainer_box")
    assert all(not url.startswith('"') for url in urls)
    assert all(not url.endswith('"') for url in urls)