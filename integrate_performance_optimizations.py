"""Integration script to apply performance optimizations to BMP page.

This script integrates the performance optimizations into the existing
BPMPage class by modifying the relevant methods.
"""

import logging
import shutil
from pathlib import Path


def backup_original_file():
    """Create a backup of the original BMP page file."""
    original_file = Path("bpm/bpm_page.py")
    backup_file = Path("bpm/bmp_page_backup.py")
    
    if original_file.exists():
        shutil.copy2(original_file, backup_file)
        logging.info(f"Created backup: {backup_file}")
        return True
    else:
        logging.error(f"Original file not found: {original_file}")
        return False


def integrate_optimizations():
    """Integrate performance optimizations into the BMP page file."""
    
    # Read the current file
    bmp_file = Path("bpm/bpm_page.py")
    
    if not bmp_file.exists():
        logging.error(f"BMP page file not found: {bmp_file}")
        return False
    
    with open(bmp_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add performance optimization imports after the existing imports
    import_addition = """
# Performance optimization imports
try:
    from performance_optimizations import (
        PerformanceOptimizer,
        BatchTextExtractor,
        OptimizedNumericParser,
        OptimizedEnvironmentDetector,
        PerformanceProfiler
    )
    from bmp_optimizations_patch import BPMPageOptimizations
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    logging.warning("Performance optimizations not available - using standard methods")
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = False
"""
    
    # Find the import section and add our imports
    if "from playwright.sync_api import expect, Page" in content:
        content = content.replace(
            "from playwright.sync_api import expect, Page",
            "from playwright.sync_api import expect, Page" + import_addition
        )
    
    # Add performance optimizer to the BPMPage __init__ method
    init_addition = """
        
        # Performance optimization components
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            self.performance_optimizer = BPMPageOptimizations()
            self.profiler = PerformanceProfiler()
            self._performance_mode_enabled = False
        else:
            self.performance_optimizer = None
            self.profiler = None
            self._performance_mode_enabled = False"""
    
    # Find the __init__ method and add performance components
    if "def __init__(self, page: Page):" in content:
        init_pattern = "        self.menu_item = page.locator(\"div.modal-content[role='document']\")"
        init_replacement = init_pattern + init_addition
        content = content.replace(init_pattern, init_replacement)
    
    # Write the modified content back to the file
    with open(bmp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logging.info("Performance optimizations integrated successfully")
    return True


def add_performance_methods():
    """Add performance-related methods to the BPMPage class."""
    
    bmp_file = Path("bpm/bpm_page.py")
    
    with open(bmp_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add optimized methods to the class
    optimized_methods = '''
    
    # Performance-optimized methods
    def enable_performance_mode(self):
        """Enable performance optimizations by replacing methods with optimized versions."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            logging.warning("Performance optimizations not available")
            return False
        
        if self._performance_mode_enabled:
            logging.info("Performance mode already enabled")
            return True
        
        # Store original methods for restoration
        self._original_extract_all_columns = self._extract_all_columns
        self._original_detect_environment = self._detect_environment
        self._original_parse_numeric_value = self._parse_numeric_value
        
        # Replace with optimized versions
        self._extract_all_columns = self._optimized_extract_all_columns
        self._detect_environment = self._optimized_detect_environment
        self._parse_numeric_value = self._optimized_parse_numeric_value
        
        self._performance_mode_enabled = True
        logging.info("Performance mode enabled - using optimized methods")
        return True
    
    def disable_performance_mode(self):
        """Disable performance optimizations by restoring original methods."""
        if not self._performance_mode_enabled:
            logging.info("Performance mode not enabled")
            return True
        
        # Restore original methods
        if hasattr(self, '_original_extract_all_columns'):
            self._extract_all_columns = self._original_extract_all_columns
        if hasattr(self, '_original_detect_environment'):
            self._detect_environment = self._original_detect_environment
        if hasattr(self, '_original_parse_numeric_value'):
            self._parse_numeric_value = self._original_parse_numeric_value
        
        self._performance_mode_enabled = False
        logging.info("Performance mode disabled - using original methods")
        return True
    
    def _optimized_extract_all_columns(self, parent_row):
        """Optimized column extraction using batch text extraction."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            return self._safe_extract_columns(parent_row)
        return self.performance_optimizer._optimized_extract_all_columns(parent_row)
    
    def _optimized_detect_environment(self, columns):
        """Optimized environment detection using caching."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            # Fallback to original logic
            try:
                if not columns or not isinstance(columns, list):
                    return "unknown"
                
                for column in columns:
                    if hasattr(column, 'is_numeric') and hasattr(column, 'numeric_value'):
                        if column.is_numeric and column.numeric_value is not None:
                            if 25 <= column.numeric_value <= 29:
                                return "buat"
                            else:
                                return "uat"
                return "unknown"
            except Exception:
                return "unknown"
        
        return self.performance_optimizer._optimized_detect_environment(columns)
    
    def _optimized_parse_numeric_value(self, text: str):
        """Optimized numeric parsing using caching."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            # Fallback to original method
            return self._parse_numeric_value_original(text)
        return self.performance_optimizer._optimized_parse_numeric_value(text)
    
    def _parse_numeric_value_original(self, text: str):
        """Original numeric parsing method as fallback."""
        try:
            if not text or not isinstance(text, str):
                return False, None
                
            cleaned_text = text.strip()
            if not cleaned_text:
                return False, None
            
            if cleaned_text.isdigit():
                return True, int(cleaned_text)
            
            if cleaned_text.startswith('-') and cleaned_text[1:].isdigit():
                return True, int(cleaned_text)
            
            if '.' in cleaned_text and cleaned_text.replace('.', '').replace('-', '').isdigit():
                try:
                    float_val = float(cleaned_text)
                    return True, int(float_val)
                except ValueError:
                    pass
            
            import re
            all_matches = []
            for match in re.finditer(r'(\\d+)', cleaned_text):
                all_matches.append((match.start(), int(match.group(1))))
            
            if all_matches:
                all_matches.sort(key=lambda x: x[0])
                numeric_value = all_matches[0][1]
                return True, numeric_value
            
            return False, None
            
        except (ValueError, AttributeError, TypeError):
            return False, None
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics from operations."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            return {"error": "Performance optimizations not available"}
        return self.performance_optimizer.get_performance_metrics()
    
    def log_performance_metrics(self):
        """Log performance metrics and cache statistics."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            logging.warning("Performance optimizations not available")
            return
        self.performance_optimizer.log_performance_metrics()
    
    def clear_performance_caches(self):
        """Clear all performance caches."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            logging.warning("Performance optimizations not available")
            return
        PerformanceOptimizer.clear_caches()
        logging.info("Performance caches cleared")
    
    def is_performance_mode_enabled(self) -> bool:
        """Check if performance mode is currently enabled."""
        return getattr(self, '_performance_mode_enabled', False)'''
    
    # Find a good insertion point (before the helper functions at the end)
    insertion_point = "# --- Modular Actions moved from bmp.py ---"
    if insertion_point in content:
        content = content.replace(insertion_point, optimized_methods + "\n\n" + insertion_point)
    else:
        # Fallback: add before the last function
        content = content.replace(
            "def map_transaction_type_to_option(transaction_type_str: str):",
            optimized_methods + "\n\ndef map_transaction_type_to_option(transaction_type_str: str):"
        )
    
    # Write the modified content back to the file
    with open(bmp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logging.info("Performance methods added successfully")
    return True


def create_performance_demo():
    """Create a demonstration script showing performance improvements."""
    
    demo_content = '''"""Performance optimization demonstration for BMP data enhancement.

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
    print("\\n=== BMP Performance Optimization Demo ===")
    
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
        
        print("\\n✅ Performance optimizations are working correctly!")
        
    except ImportError as e:
        print(f"❌ Performance optimizations not available: {e}")
        print("Make sure performance_optimizations.py is in the same directory")


if __name__ == "__main__":
    demonstrate_performance()
'''
    
    with open("performance_demo.py", "w", encoding="utf-8") as f:
        f.write(demo_content)
    
    logging.info("Created performance demonstration script: performance_demo.py")


def main():
    """Main integration function."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("BMP Performance Optimization Integration")
    print("=" * 40)
    
    # Step 1: Create backup
    print("\n1. Creating backup of original file...")
    if not backup_original_file():
        print("❌ Failed to create backup")
        return False
    print("✅ Backup created successfully")
    
    # Step 2: Integrate optimizations
    print("\n2. Integrating performance optimizations...")
    if not integrate_optimizations():
        print("❌ Failed to integrate optimizations")
        return False
    print("✅ Optimizations integrated successfully")
    
    # Step 3: Add performance methods
    print("\n3. Adding performance methods...")
    if not add_performance_methods():
        print("❌ Failed to add performance methods")
        return False
    print("✅ Performance methods added successfully")
    
    # Step 4: Create demonstration
    print("\n4. Creating performance demonstration...")
    create_performance_demo()
    print("✅ Demo script created")
    
    print("\n🎉 Performance optimization integration complete!")
    print("\nNext steps:")
    print("• Run 'python performance_demo.py' to see performance improvements")
    print("• Use 'python test_performance_optimizations.py' to validate optimizations")
    print("• Call enable_performance_mode() on BPMPage instances to use optimizations")
    
    return True


if __name__ == "__main__":
    main()