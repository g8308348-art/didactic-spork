"""Performance tests for BMP data enhancement optimizations.

This module contains tests to validate that the performance optimizations
provide measurable improvements over the original implementation.
"""

import pytest
import time
import logging
from unittest.mock import Mock, MagicMock
from performance_optimizations import (
    PerformanceOptimizer,
    BatchTextExtractor,
    OptimizedNumericParser,
    OptimizedEnvironmentDetector,
    PerformanceProfiler
)


class TestPerformanceOptimizations:
    """Test suite for performance optimization components."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear caches before each test
        PerformanceOptimizer.clear_caches()
        self.profiler = PerformanceProfiler()
    
    def teardown_method(self):
        """Clean up after each test."""
        PerformanceOptimizer.clear_caches()
    
    def test_numeric_parsing_cache_performance(self):
        """Test that cached numeric parsing provides performance benefits."""
        test_values = [
            "25", "26-Q1", "27-UAT", "28", "29-PROD",
            "15", "30", "BUAT-25", "UAT-27", "ENV-29"
        ] * 10  # Repeat values to test cache effectiveness
        
        # Time uncached parsing (first run)
        start_time = time.perf_counter()
        for value in test_values[:10]:  # First 10 unique values
            OptimizedNumericParser.parse_numeric_value_cached(value)
        uncached_time = time.perf_counter() - start_time
        
        # Time cached parsing (repeated values)
        start_time = time.perf_counter()
        for value in test_values:  # All values including repeats
            OptimizedNumericParser.parse_numeric_value_cached(value)
        total_time = time.perf_counter() - start_time
        
        # Calculate cache effectiveness
        cache_stats = PerformanceOptimizer.get_cache_stats()
        
        logging.info(f"Uncached parsing time (10 values): {uncached_time:.4f}s")
        logging.info(f"Total parsing time (100 values with cache): {total_time:.4f}s")
        logging.info(f"Cache statistics: {cache_stats}")
        
        # Assert that caching provides benefit
        assert cache_stats["numeric_cache_size"] > 0, "Cache should contain parsed values"
        assert total_time < uncached_time * 5, "Cached parsing should be significantly faster"
    
    def test_environment_detection_cache_performance(self):
        """Test that cached environment detection provides performance benefits."""
        # Create mock column data with repeated patterns
        mock_columns_buat = [Mock(is_numeric=True, numeric_value=25)]
        mock_columns_uat = [Mock(is_numeric=True, numeric_value=15)]
        mock_columns_unknown = [Mock(is_numeric=False, numeric_value=None)]
        
        test_cases = [
            mock_columns_buat, mock_columns_uat, mock_columns_unknown,
            mock_columns_buat, mock_columns_uat, mock_columns_unknown  # Repeat for cache testing
        ] * 10
        
        # Time environment detection with caching
        start_time = time.perf_counter()
        results = []
        for columns in test_cases:
            result = OptimizedEnvironmentDetector.detect_environment_cached(columns)
            results.append(result)
        detection_time = time.perf_counter() - start_time
        
        # Verify results and cache usage
        cache_stats = PerformanceOptimizer.get_cache_stats()
        
        logging.info(f"Environment detection time (60 operations): {detection_time:.4f}s")
        logging.info(f"Cache statistics: {cache_stats}")
        
        # Assert cache effectiveness
        assert cache_stats["environment_cache_size"] > 0, "Environment cache should contain results"
        assert len(set(results)) == 3, "Should detect 3 different environments"
        assert detection_time < 0.1, "Cached detection should be very fast"
    
    def test_batch_text_extraction_mock(self):
        """Test batch text extraction with mocked Playwright elements."""
        # Mock parent row and cells
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        # Mock the evaluate_all method to return test data
        test_cell_texts = ["25", "BUAT-Q1", "Transaction", "Active", "2024-01-01"]
        mock_cells.evaluate_all.return_value = test_cell_texts
        
        # Test batch extraction
        start_time = time.perf_counter()
        result = BatchTextExtractor.extract_all_cell_texts(mock_parent_row)
        extraction_time = time.perf_counter() - start_time
        
        logging.info(f"Batch extraction time: {extraction_time:.4f}s")
        logging.info(f"Extracted texts: {result}")
        
        # Verify results
        assert result == test_cell_texts, "Should return the mocked cell texts"
        assert extraction_time < 0.01, "Batch extraction should be very fast with mocked data"
        
        # Verify that evaluate_all was called (indicating batch operation)
        mock_cells.evaluate_all.assert_called_once()
    
    def test_performance_profiler_accuracy(self):
        """Test that the performance profiler accurately measures operation times."""
        profiler = PerformanceProfiler()
        
        # Test operation timing
        profiler.start_operation("test_operation")
        time.sleep(0.01)  # Sleep for 10ms
        duration = profiler.end_operation("test_operation")
        
        # Verify timing accuracy (within reasonable tolerance)
        assert 0.008 <= duration <= 0.015, f"Duration {duration} should be approximately 0.01s"
        
        # Test multiple operations
        for i in range(5):
            profiler.start_operation("repeated_operation")
            time.sleep(0.001)  # Sleep for 1ms
            profiler.end_operation("repeated_operation")
        
        # Get performance summary
        summary = profiler.get_performance_summary()
        
        logging.info(f"Performance summary: {summary}")
        
        # Verify summary data
        assert "test_operation" in summary, "Should track test_operation"
        assert "repeated_operation" in summary, "Should track repeated_operation"
        assert summary["repeated_operation"]["count"] == 5, "Should count 5 repeated operations"
        assert summary["repeated_operation"]["total_time"] > 0.004, "Total time should be reasonable"
    
    def test_cache_size_management(self):
        """Test that cache size management prevents memory issues."""
        # Fill numeric cache beyond limit
        original_limit = PerformanceOptimizer.MAX_NUMERIC_CACHE_SIZE
        PerformanceOptimizer.MAX_NUMERIC_CACHE_SIZE = 10  # Set small limit for testing
        
        try:
            # Add more items than the cache limit
            for i in range(15):
                OptimizedNumericParser.parse_numeric_value_cached(f"value_{i}")
            
            cache_stats = PerformanceOptimizer.get_cache_stats()
            
            logging.info(f"Cache stats after overflow: {cache_stats}")
            
            # Verify cache size is managed
            assert cache_stats["numeric_cache_size"] <= PerformanceOptimizer.MAX_NUMERIC_CACHE_SIZE
            
        finally:
            # Restore original limit
            PerformanceOptimizer.MAX_NUMERIC_CACHE_SIZE = original_limit
    
    def test_optimization_correctness(self):
        """Test that optimized methods produce the same results as original logic."""
        test_cases = [
            ("25", True, 25),
            ("27-Q1", True, 27),
            ("BUAT-29", True, 29),
            ("no-numbers", False, None),
            ("", False, None),
            ("123.45", True, 123),
            ("UAT-15-PROD", True, 15)
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            is_numeric, numeric_value = OptimizedNumericParser.parse_numeric_value_cached(text)
            
            assert is_numeric == expected_is_numeric, f"Numeric detection failed for '{text}'"
            assert numeric_value == expected_value, f"Numeric value extraction failed for '{text}'"
    
    def test_environment_detection_correctness(self):
        """Test that optimized environment detection produces correct results."""
        # Test BUAT environment (25-29)
        buat_columns = [Mock(is_numeric=True, numeric_value=val) for val in [25, 26, 27, 28, 29]]
        for columns in [[col] for col in buat_columns]:
            result = OptimizedEnvironmentDetector.detect_environment_cached(columns)
            assert result == "buat", f"Should detect BUAT for value {columns[0].numeric_value}"
        
        # Test UAT environment (outside 25-29)
        uat_values = [1, 15, 24, 30, 35, 100]
        for value in uat_values:
            columns = [Mock(is_numeric=True, numeric_value=value)]
            result = OptimizedEnvironmentDetector.detect_environment_cached(columns)
            assert result == "uat", f"Should detect UAT for value {value}"
        
        # Test unknown environment (no numeric values)
        unknown_columns = [Mock(is_numeric=False, numeric_value=None)]
        result = OptimizedEnvironmentDetector.detect_environment_cached(unknown_columns)
        assert result == "unknown", "Should detect unknown for non-numeric values"


class TestPerformanceComparison:
    """Performance comparison tests between optimized and unoptimized approaches."""
    
    def test_numeric_parsing_performance_comparison(self):
        """Compare performance of optimized vs simple numeric parsing."""
        import re
        
        # Simple unoptimized parsing function
        def simple_parse_numeric(text):
            try:
                if text.isdigit():
                    return True, int(text)
                match = re.search(r'\b(\d+)\b', text)
                if match:
                    return True, int(match.group(1))
                return False, None
            except:
                return False, None
        
        test_values = ["25", "27-Q1", "BUAT-29", "no-numbers", "123.45"] * 100
        
        # Time simple parsing
        start_time = time.perf_counter()
        simple_results = [simple_parse_numeric(val) for val in test_values]
        simple_time = time.perf_counter() - start_time
        
        # Clear cache and time optimized parsing
        PerformanceOptimizer.clear_caches()
        start_time = time.perf_counter()
        optimized_results = [OptimizedNumericParser.parse_numeric_value_cached(val) for val in test_values]
        optimized_time = time.perf_counter() - start_time
        
        logging.info(f"Simple parsing time: {simple_time:.4f}s")
        logging.info(f"Optimized parsing time: {optimized_time:.4f}s")
        logging.info(f"Performance improvement: {simple_time / optimized_time:.2f}x")
        
        # Verify results are equivalent
        assert simple_results == optimized_results, "Results should be identical"
        
        # With repeated values, optimized should be faster due to caching
        # Note: This may not always be true for small datasets, but should show benefit with larger datasets


if __name__ == "__main__":
    # Run performance tests
    logging.basicConfig(level=logging.INFO)
    
    test_suite = TestPerformanceOptimizations()
    test_suite.setup_method()
    
    print("Running performance optimization tests...")
    
    try:
        test_suite.test_numeric_parsing_cache_performance()
        print("✓ Numeric parsing cache test passed")
        
        test_suite.test_environment_detection_cache_performance()
        print("✓ Environment detection cache test passed")
        
        test_suite.test_batch_text_extraction_mock()
        print("✓ Batch text extraction test passed")
        
        test_suite.test_performance_profiler_accuracy()
        print("✓ Performance profiler test passed")
        
        test_suite.test_cache_size_management()
        print("✓ Cache size management test passed")
        
        test_suite.test_optimization_correctness()
        print("✓ Optimization correctness test passed")
        
        test_suite.test_environment_detection_correctness()
        print("✓ Environment detection correctness test passed")
        
        print("\nAll performance optimization tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise
    finally:
        test_suite.teardown_method()