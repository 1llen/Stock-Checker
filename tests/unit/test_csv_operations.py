import pytest
from pathlib import Path

def test_get_url_list(sample_stock_checker, create_test_csv):
    """Test getting multiple URLs for a key"""
    urls = sample_stock_checker.get_url_list("test_urls.csv", "test_exist")
    assert len(urls) == 2
    assert all(url.startswith('https://example.com/etb') for url in urls)

def test_get_url_nonexistent_key(sample_stock_checker, create_test_csv):
    """Test getting URL for non-existent key"""
    urls = sample_stock_checker.get_url_list("test_urls.csv", "nonexistent")
    assert len(urls) == 0

def test_get_url_missing_file(sample_stock_checker):
    """Test handling of missing CSV file"""
    with pytest.raises(FileNotFoundError):
        sample_stock_checker.get_url_list("nonexistent.csv", "any_key")
