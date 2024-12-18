import pytest
from pathlib import Path
import csv

@pytest.fixture
def test_csv_path():
    """Fixture to provide test CSV file path"""
    return Path(__file__).parent / "test_data" / "test_products.csv"

@pytest.fixture
def sample_stock_checker():
    """Fixture to provide a StockChecker instance"""
    from stock_checker import StockChecker
    return StockChecker(check_interval=1)  # Short interval for testing

@pytest.fixture
def create_test_csv(test_csv_path):
    """Fixture to create a temporary test CSV file"""
    test_data = [
        ['key', 'url'],
        ['elite_trainer_box', 'https://example.com/etb1'],
        ['elite_trainer_box', 'https://example.com/etb2'],
        ['booster_bundle', 'https://example.com/bb1'],
    ]
    
    test_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
    
    yield test_csv_path
    
    # Cleanup
    if test_csv_path.exists():
        test_csv_path.unlink()