import pytest
from pathlib import Path

def test_get_url_list(sample_stock_checker, create_test_csv):
    """Test getting multiple URLs for a key"""
    urls = sample_stock_checker.get_url_list("test_urls.csv", "product_type_1")
    assert len(urls) == 3  # Assuming 3 stores have product_type_1
    
    # Check that each URL entry has the correct structure
    for entry in urls:
        assert isinstance(entry, dict)
        assert 'url' in entry
        assert 'site_name' in entry
        assert entry['url'].startswith('https://teststore')
        assert entry['site_name'].startswith('TestStore')

def test_get_url_list_single_entry(sample_stock_checker, create_test_csv):
    """Test getting URLs for a key that exists in only one store"""
    urls = sample_stock_checker.get_url_list("test_urls.csv", "product_type_3")
    assert len(urls) == 2
    assert urls[0]['site_name'] in ['TestStore1', 'TestStore3']
    assert urls[1]['site_name'] in ['TestStore1', 'TestStore3']
    assert urls[0]['url'].endswith('test-product-3')

def test_get_url_nonexistent_key(sample_stock_checker, create_test_csv):
    """Test getting URL for non-existent key"""
    urls = sample_stock_checker.get_url_list("test_urls.csv", "nonexistent")
    assert len(urls) == 0

def test_get_url_missing_file(sample_stock_checker):
    """Test handling of missing CSV file"""
    with pytest.raises(FileNotFoundError):
        sample_stock_checker.get_url_list("nonexistent.csv", "any_key")

def test_get_url_invalid_csv_format(sample_stock_checker, tmp_path):
    """Test handling of CSV with invalid format"""
    # Create a CSV file with wrong columns
    invalid_csv = tmp_path / "invalid.csv"
    invalid_csv.write_text("key,invalid_column\nproduct_type_1,some_value")
    
    with pytest.raises(KeyError):
        sample_stock_checker.get_url_list(str(invalid_csv), "product_type_1")

# Update the fixture to create test CSV with new format
@pytest.fixture
def create_test_csv(tmp_path):
    """Create a temporary test CSV file with the new format"""
    csv_content = """key,site_name,url
product_type_1,TestStore1,https://teststore1.com/products/test-product-1
product_type_1,TestStore2,https://teststore2.com/products/test-product-1
product_type_1,TestStore3,https://teststore3.com/products/test-product-1
product_type_2,TestStore1,https://teststore1.com/products/test-product-2
product_type_2,TestStore2,https://teststore2.com/products/test-product-2
product_type_3,TestStore1,https://teststore1.com/products/test-product-3
product_type_3,TestStore3,https://teststore3.com/products/test-product-3"""
    
    test_csv = tmp_path / "test_urls.csv"
    test_csv.write_text(csv_content)
    return test_csv