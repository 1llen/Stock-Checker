import pytest
from tests.test_data.mock_html_responses import (
    MOCK_IN_STOCK_HTML,
    MOCK_OUT_OF_STOCK_HTML,
    MOCK_MULTIPLE_BUTTONS_HTML,
    MOCK_NO_BUTTON_HTML
)

def test_parse_stock_status_in_stock(sample_stock_checker):
    """Test parsing HTML with in-stock product"""
    is_in_stock, product_name, site_name = sample_stock_checker.parse_stock_status(
        MOCK_IN_STOCK_HTML,
        "TestStore"
    )
    assert is_in_stock is True
    assert product_name == "Test Product Name"
    assert site_name == "TestStore"

def test_parse_stock_status_out_of_stock(sample_stock_checker):
    """Test parsing HTML with out-of-stock product"""
    is_in_stock, product_name, site_name = sample_stock_checker.parse_stock_status(
        MOCK_OUT_OF_STOCK_HTML,
        "TestStore"
    )
    assert is_in_stock is False
    assert product_name == "Test Product Name"
    assert site_name == "TestStore"

def test_parse_stock_status_multiple_buttons(sample_stock_checker):
    """Test parsing HTML with multiple submit buttons"""
    is_in_stock, product_name, site_name = sample_stock_checker.parse_stock_status(
        MOCK_MULTIPLE_BUTTONS_HTML,
        "TestStore"
    )
    assert is_in_stock is False
    assert product_name == "Test Product Name"
    assert site_name == "TestStore"

def test_parse_stock_status_no_button(sample_stock_checker):
    """Test parsing HTML with no submit buttons"""
    is_in_stock, product_name, site_name = sample_stock_checker.parse_stock_status(
        MOCK_NO_BUTTON_HTML,
        "TestStore"
    )
    assert is_in_stock is False
    assert product_name == "Test Product Name"
    assert site_name == "TestStore"

def test_parse_stock_status_invalid_html(sample_stock_checker):
    """Test parsing invalid HTML"""
    is_in_stock, product_name, site_name = sample_stock_checker.parse_stock_status(
        "",
        "TestStore"
    )
    assert is_in_stock is None
    assert product_name is None
    assert site_name is None