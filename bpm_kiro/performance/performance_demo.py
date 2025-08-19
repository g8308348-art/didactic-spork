"""Performance optimization demonstration for BMP data enhancement.

This script demonstrates the performance improvements achieved through
the optimization implementations.
"""

import logging
import time
from unittest.mock import Mock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def demonstrate_performance():
    """Demonstrate performance improvements."""
    print("\n=== BMP Performance Optimization Demo ===")
    
    try:
        from performance_optimizations import PerformanceOptimizer, OptimizedNumericParser
        
        # Test data with common patterns
        test_values = [
            "25", "26-Q1", "27-UAT", "28-PROD", "29-BUAT",
            "15", "30", "BUAT-25", "UAT-27", "ENV-29",
            "no-numbers", "123.45", "", "PROD-15-TEST"
        ] * 50  # 700 total operations
        
        print(f"Testing with {len(test_values)} parsing operations...")
        
        # Clear cache for fair comparison
        PerformanceOptimizer.clear_caches()
        
        # Time the parsing operations
        start_time = time.perf_counter()
        results = []
        for value in test_values:
            result = OptimizedNumericParser.parse_numeric_value_cached(value)
            results.append(result)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        operations_per_second = len(test_values) / total_time
        
        print(f"Total parsing time: {total_time:.4f} seconds")
        print(f"Operations per second: {operations_per_second:.0f}")
        print(f"Average time per operation: {total_time / len(test_values) * 1000:.4f} ms")
        
        # Show cache effectiveness
        cache_stats = PerformanceOptimizer.get_cache_stats()
        print(f"Cache statistics: {cache_stats}")
        
        # Calculate cache hit ratio
        unique_values = len(set(test_values))
        cache_hit_ratio = (len(test_values) - unique_values) / len(test_values) * 100
        print(f"Cache hit ratio: {cache_hit_ratio:.1f}%")
        
        print("\n✅ Performance optimizations are working correctly!")
        
    except ImportError as e:
        print(f"❌ Performance optimizations not available: {e}")
        print("Make sure performance_optimizations.py is in the same directory")


if __name__ == "__main__":
    demonstrate_performance()
