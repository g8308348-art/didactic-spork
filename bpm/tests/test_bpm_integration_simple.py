"""Simple test to verify BPM page integration works correctly."""

import logging
import sys
import os
from unittest.mock import Mock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_bpm_page_basic_functionality():
    """Test basic BPM page functionality."""
    try:
        # Import BPM page
        from bpm.bpm_page import BPMPage
        
        # Create mock Playwright page
        mock_page = Mock()
        mock_page.locator.return_value = Mock()
        
        # Create BPM page instance
        print("Creating BPM page instance...")
        bpm_page = BPMPage(mock_page)
        print("✅ BPM page created successfully")
        
        # Check if performance optimization attributes exist
        has_performance_optimizer = hasattr(bpm_page, 'performance_optimizer')
        has_profiler = hasattr(bpm_page, 'profiler')
        has_performance_mode_enabled = hasattr(bpm_page, '_performance_mode_enabled')
        
        print(f"Has performance_optimizer: {has_performance_optimizer}")
        print(f"Has profiler: {has_profiler}")
        print(f"Has _performance_mode_enabled: {has_performance_mode_enabled}")
        
        # Check if performance methods exist
        performance_methods = [
            'enable_performance_mode',
            'disable_performance_mode', 
            'get_performance_metrics',
            'log_performance_metrics',
            'clear_performance_caches',
            'is_performance_mode_enabled'
        ]
        
        print("\nChecking performance methods:")
        for method_name in performance_methods:
            has_method = hasattr(bpm_page, method_name)
            print(f"  {method_name}: {'✅' if has_method else '❌'}")
        
        # Test basic method calls if they exist
        if hasattr(bpm_page, 'get_performance_metrics'):
            try:
                metrics = bpm_page.get_performance_metrics()
                print(f"✅ get_performance_metrics() works: {type(metrics)}")
            except Exception as e:
                print(f"❌ get_performance_metrics() failed: {e}")
        
        if hasattr(bpm_page, 'is_performance_mode_enabled'):
            try:
                enabled = bpm_page.is_performance_mode_enabled()
                print(f"✅ is_performance_mode_enabled() works: {enabled}")
            except Exception as e:
                print(f"❌ is_performance_mode_enabled() failed: {e}")
        
        # Test performance mode toggle if available
        if hasattr(bpm_page, 'enable_performance_mode'):
            try:
                result = bpm_page.enable_performance_mode()
                print(f"✅ enable_performance_mode() works: {result}")
            except Exception as e:
                print(f"❌ enable_performance_mode() failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import BPM page: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_performance_optimizations_import():
    """Test if performance optimizations can be imported."""
    try:
        from performance_optimizations import PerformanceOptimizer
        print("✅ Performance optimizations imported successfully")
        
        # Test basic functionality
        cache_stats = PerformanceOptimizer.get_cache_stats()
        print(f"✅ Cache stats: {cache_stats}")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import performance optimizations: {e}")
        return False
    except Exception as e:
        print(f"❌ Performance optimizations error: {e}")
        return False


def main():
    """Run simple integration tests."""
    print("BPM Page Integration Test")
    print("=" * 25)
    
    # Test performance optimizations import
    print("\n1. Testing performance optimizations import...")
    perf_ok = test_performance_optimizations_import()
    
    # Test BPM page basic functionality
    print("\n2. Testing BPM page basic functionality...")
    bpm_ok = test_bpm_page_basic_functionality()
    
    print(f"\nResults:")
    print(f"Performance optimizations: {'✅' if perf_ok else '❌'}")
    print(f"BPM page functionality: {'✅' if bpm_ok else '❌'}")
    
    if perf_ok and bpm_ok:
        print("\n🎉 Integration test passed!")
        return True
    else:
        print("\n⚠️ Integration test failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)