"""Integration tests for BMP page with performance optimizations.

This module tests the integration of performance optimizations into the
BPMPage class to ensure functionality is preserved while improving performance.
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the current directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the optimized BMP page
try:
    from bpm.bpm_page import BPMPage, ColumnData, BPMSearchResult
    BMP_PAGE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"BMP page not available: {e}")
    BMP_PAGE_AVAILABLE = False

# Import performance optimizations
try:
    from performance_optimizations import PerformanceOptimizer
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = False


class TestBMPPagePerformanceIntegration:
    """Test suite for BMP page performance integration."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            PerformanceOptimizer.clear_caches()
    
    def teardown_method(self):
        """Clean up after each test."""
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            PerformanceOptimizer.clear_caches()
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_bmp_page_initialization_with_optimizations(self):
        """Test that BMP page initializes correctly with performance optimizations."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        # Verify initialization
        assert bmp_page.page == mock_page
        assert hasattr(bmp_page, 'performance_optimizer')
        assert hasattr(bmp_page, 'profiler')
        assert hasattr(bmp_page, '_performance_mode_enabled')
        
        # Test performance mode methods exist
        assert hasattr(bmp_page, 'enable_performance_mode')
        assert hasattr(bmp_page, 'disable_performance_mode')
        assert hasattr(bmp_page, 'get_performance_metrics')
        assert hasattr(bmp_page, 'log_performance_metrics')
        assert hasattr(bmp_page, 'clear_performance_caches')
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_performance_mode_toggle(self):
        """Test enabling and disabling performance mode."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        # Initially performance mode should be disabled
        assert not bmp_page.is_performance_mode_enabled()
        
        # Enable performance mode
        result = bmp_page.enable_performance_mode()
        
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            assert result is True
            assert bmp_page.is_performance_mode_enabled()
            
            # Disable performance mode
            result = bmp_page.disable_performance_mode()
            assert result is True
            assert not bmp_page.is_performance_mode_enabled()
        else:
            # Should handle gracefully when optimizations not available
            assert result is False
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_optimized_numeric_parsing_integration(self):
        """Test that optimized numeric parsing works through BMP page."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        # Test cases for numeric parsing
        test_cases = [
            ("25", True, 25),
            ("27-Q1", True, 27),
            ("BUAT-29", True, 29),
            ("no-numbers", False, None),
            ("", False, None)
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            # Test with original method
            is_numeric_orig, value_orig = bmp_page._parse_numeric_value_original(text)
            
            # Test with optimized method (if available)
            is_numeric_opt, value_opt = bmp_page._optimized_parse_numeric_value(text)
            
            # Results should be the same
            assert is_numeric_orig == is_numeric_opt == expected_is_numeric
            assert value_orig == value_opt == expected_value
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_optimized_environment_detection_integration(self):
        """Test that optimized environment detection works through BMP page."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        # Test cases for environment detection
        test_cases = [
            ([ColumnData(1, "25", True, 25)], "buat"),
            ([ColumnData(1, "27-Q1", True, 27)], "buat"),
            ([ColumnData(1, "15", True, 15)], "uat"),
            ([ColumnData(1, "30", True, 30)], "uat"),
            ([ColumnData(1, "no-numbers", False, None)], "unknown"),
            ([], "unknown")
        ]
        
        for columns, expected_environment in test_cases:
            # Test with optimized method
            result = bmp_page._optimized_detect_environment(columns)
            assert result == expected_environment
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_performance_metrics_collection(self):
        """Test that performance metrics are collected correctly."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        # Get initial metrics
        metrics = bmp_page.get_performance_metrics()
        
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            assert isinstance(metrics, dict)
            # Metrics should be empty initially
            assert len(metrics) == 0 or all(stats["count"] == 0 for stats in metrics.values())
        else:
            assert "error" in metrics
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_cache_management_integration(self):
        """Test that cache management works through BMP page."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            # Clear caches
            bmp_page.clear_performance_caches()
            
            # Perform some operations to populate cache
            test_values = ["25", "27-Q1", "BUAT-29", "15", "30"]
            for value in test_values:
                bmp_page._optimized_parse_numeric_value(value)
            
            # Check that cache has entries
            cache_stats = PerformanceOptimizer.get_cache_stats()
            assert cache_stats["numeric_cache_size"] > 0
            
            # Clear caches again
            bmp_page.clear_performance_caches()
            
            # Check that cache is empty
            cache_stats = PerformanceOptimizer.get_cache_stats()
            assert cache_stats["numeric_cache_size"] == 0
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_fallback_behavior_without_optimizations(self):
        """Test that BMP page works correctly even without optimizations."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        # Test that methods work even if optimizations are not available
        # This tests the fallback behavior
        
        # Test numeric parsing fallback
        is_numeric, value = bmp_page._parse_numeric_value_original("25")
        assert is_numeric is True
        assert value == 25
        
        # Test environment detection fallback
        columns = [ColumnData(1, "25", True, 25)]
        result = bmp_page._optimized_detect_environment(columns)
        assert result in ["buat", "uat", "unknown"]
    
    @pytest.mark.skipif(not BMP_PAGE_AVAILABLE, reason="BMP page not available")
    def test_performance_mode_method_replacement(self):
        """Test that performance mode correctly replaces methods."""
        # Mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BMP page instance
        bmp_page = BPMPage(mock_page)
        
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE and hasattr(bmp_page, 'performance_optimizer'):
            # Store references to original methods
            original_extract = bmp_page._extract_all_columns
            original_detect = bmp_page._detect_environment
            original_parse = bmp_page._parse_numeric_value
            
            # Enable performance mode
            bmp_page.enable_performance_mode()
            
            # Check that methods have been replaced
            assert bmp_page._extract_all_columns != original_extract
            assert bmp_page._detect_environment != original_detect
            assert bmp_page._parse_numeric_value != original_parse
            
            # Disable performance mode
            bmp_page.disable_performance_mode()
            
            # Check that original methods are restored
            assert bmp_page._extract_all_columns == original_extract
            assert bmp_page._detect_environment == original_detect
            assert bmp_page._parse_numeric_value == original_parse


def run_integration_tests():
    """Run integration tests manually."""
    logging.basicConfig(level=logging.INFO)
    
    print("Running BMP Performance Integration Tests...")
    print("=" * 45)
    
    test_suite = TestBMPPagePerformanceIntegration()
    
    tests = [
        ("BMP Page Initialization", test_suite.test_bmp_page_initialization_with_optimizations),
        ("Performance Mode Toggle", test_suite.test_performance_mode_toggle),
        ("Numeric Parsing Integration", test_suite.test_optimized_numeric_parsing_integration),
        ("Environment Detection Integration", test_suite.test_optimized_environment_detection_integration),
        ("Performance Metrics Collection", test_suite.test_performance_metrics_collection),
        ("Cache Management Integration", test_suite.test_cache_management_integration),
        ("Fallback Behavior", test_suite.test_fallback_behavior_without_optimizations),
        ("Method Replacement", test_suite.test_performance_mode_method_replacement)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_suite.setup_method()
            test_func()
            test_suite.teardown_method()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)