import pytest
from tests.test_data.mock_html_responses import MOCK_IN_STOCK_HTML, MOCK_OUT_OF_STOCK_HTML

def test_parse_stock_status_in_stock(sample_stock_checker):
    """Test parsing HTML with in-stock product"""
    is_in_stock, product_name = sample_stock_checker.parse_stock_status(MOCK_IN_STOCK_HTML)
    assert is_in_stock is True
    assert product_name == "Pokemon Elite Trainer Box"

def test_parse_stock_status_out_of_stock(sample_stock_checker):
    """Test parsing HTML with out-of-stock product"""
    is_in_stock, product_name = sample_stock_checker.parse_stock_status(MOCK_OUT_OF_STOCK_HTML)
    assert is_in_stock is False
    assert product_name == "Pokemon Elite Trainer Box"

def test_parse_stock_status_invalid_html(sample_stock_checker):
    """Test parsing invalid HTML"""
    is_in_stock, product_name = sample_stock_checker.parse_stock_status("")
    assert is_in_stock is None
    assert product_name is None