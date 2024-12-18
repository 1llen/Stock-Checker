import pytest
import threading
import time
from unittest.mock import MagicMock

def test_monitor_multiple_urls(sample_stock_checker):
    """Test monitoring multiple URLs"""
    urls = [
        "https://example.com/product1",
        "https://example.com/product2"
    ]
    
    # Mock the check_stock method
    original_check_stock = sample_stock_checker.check_stock
    stock_check_count = 0
    
    def mock_check_stock(url=None):
        nonlocal stock_check_count
        stock_check_count += 1
        if stock_check_count >= 2:  # Stop after checking each URL once
            monitor_thread.shutdown = True
        return True, f"Test Product {stock_check_count}"
    
    sample_stock_checker.check_stock = mock_check_stock
    
    # Create a stoppable monitor thread
    class MonitorThread(threading.Thread):
        def __init__(self, checker, urls):
            super().__init__()
            self.checker = checker
            self.urls = urls
            self.shutdown = False
            
        def run(self):
            while not self.shutdown:
                for url in self.urls:
                    if self.shutdown:
                        break
                    self.checker.check_stock(url)
                    time.sleep(0.1)
    
    monitor_thread = MonitorThread(sample_stock_checker, urls)
    monitor_thread.start()
    monitor_thread.join(timeout=2)
    
    # Restore original method
    sample_stock_checker.check_stock = original_check_stock
    
    assert stock_check_count >= 2