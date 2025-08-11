"""Optimized methods for BMP page performance improvements.

This file contains the optimized versions of key methods that should be
integrated into the BPMPage class for improved performance.
"""

import logging
from typing import List, Optional
from performance_optimizations import (
    PerformanceOptimizer, 
    BatchTextExtractor, 
    OptimizedNumericParser,
    OptimizedEnvironmentDetector,
    PerformanceProfiler
)


class BPMPageOptimizations:
    """Optimized methods for BPMPage class."""
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
    
    def _optimized_extract_all_columns(self, parent_row):
        """Optimized column extraction using batch text extraction.
        
        This method minimizes DOM queries by extracting all cell texts in a single
        batch operation, then processing them to create ColumnData objects.
        
        Args:
            parent_row: Playwright locator for the parent row element
            
        Returns:
            List[ColumnData]: List of column data objects with optimized extraction
        """
        from bpm.bpm_page import ColumnData  # Import here to avoid circular imports
        
        self.profiler.start_operation("optimized_column_extraction")
        
        try:
            if not parent_row:
                logging.warning("No parent row provided for optimized column extraction")
                return []
            
            # Use batch text extraction for better performance
            cell_texts = BatchTextExtractor.extract_all_cell_texts(parent_row)
            
            if not cell_texts:
                logging.debug("No cell texts extracted")
                return []
            
            # Process extracted texts into ColumnData objects
            columns = []
            for i, cell_text in enumerate(cell_texts):
                try:
                    # Use optimized numeric parsing with caching
                    is_numeric, numeric_value = OptimizedNumericParser.parse_numeric_value_cached(cell_text)
                    
                    column_data = ColumnData(
                        position=i + 1,  # 1-based position
                        value=cell_text,
                        is_numeric=is_numeric,
                        numeric_value=numeric_value
                    )
                    
                    columns.append(column_data)
                    logging.debug(f"Optimized column {i+1}: '{cell_text}' (numeric: {is_numeric}, value: {numeric_value})")
                    
                except Exception as column_error:
                    logging.error(f"Error processing column {i+1}: {column_error}")
                    # Add placeholder column to maintain position consistency
                    columns.append(ColumnData(
                        position=i + 1,
                        value="ProcessingError",
                        is_numeric=False,
                        numeric_value=None
                    ))
            
            duration = self.profiler.end_operation("optimized_column_extraction")
            logging.info(f"Optimized column extraction completed: {len(columns)} columns in {duration:.4f}s")
            
            return columns
            
        except Exception as e:
            self.profiler.end_operation("optimized_column_extraction")
            logging.error(f"Critical error in optimized column extraction: {e}")
            return []
    
    def _optimized_detect_environment(self, columns) -> str:
        """Optimized environment detection using caching.
        
        Uses cached environment detection for improved performance on repeated calls
        with the same or similar column data.
        
        Args:
            columns: List of ColumnData objects to analyze
            
        Returns:
            str: Environment classification ("buat", "uat", or "unknown")
        """
        self.profiler.start_operation("optimized_environment_detection")
        
        try:
            result = OptimizedEnvironmentDetector.detect_environment_cached(columns)
            
            duration = self.profiler.end_operation("optimized_environment_detection")
            logging.info(f"Optimized environment detection completed: '{result}' in {duration:.4f}s")
            
            return result
            
        except Exception as e:
            self.profiler.end_operation("optimized_environment_detection")
            logging.error(f"Error in optimized environment detection: {e}")
            return "unknown"
    
    def _optimized_parse_numeric_value(self, text: str):
        """Optimized numeric parsing using caching and pre-compiled patterns.
        
        Args:
            text: Text to parse for numeric values
            
        Returns:
            Tuple of (is_numeric: bool, numeric_value: Optional[int])
        """
        self.profiler.start_operation("optimized_numeric_parsing")
        
        try:
            result = OptimizedNumericParser.parse_numeric_value_cached(text)
            self.profiler.end_operation("optimized_numeric_parsing")
            return result
            
        except Exception as e:
            self.profiler.end_operation("optimized_numeric_parsing")
            logging.error(f"Error in optimized numeric parsing: {e}")
            return False, None
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics from the profiler."""
        return self.profiler.get_performance_summary()
    
    def log_performance_metrics(self):
        """Log performance metrics and cache statistics."""
        self.profiler.log_performance_summary()
    
    def clear_performance_caches(self):
        """Clear all performance caches."""
        PerformanceOptimizer.clear_caches()
        logging.info("Performance caches cleared")


# Integration methods for BPMPage class
def integrate_optimizations_into_bmp_page():
    """
    Instructions for integrating optimizations into BPMPage class:
    
    1. Add the following import at the top of bpm_page.py:
       from performance_optimizations import (
           PerformanceOptimizer, 
           BatchTextExtractor, 
           OptimizedNumericParser,
           OptimizedEnvironmentDetector,
           PerformanceProfiler
       )
    
    2. Add these instance variables to BPMPage.__init__():
       self.performance_optimizer = BPMPageOptimizations()
       self.profiler = PerformanceProfiler()
    
    3. Replace the following methods with optimized versions:
       - _extract_all_columns() -> use _optimized_extract_all_columns()
       - _detect_environment() -> use _optimized_detect_environment()  
       - _parse_numeric_value() -> use _optimized_parse_numeric_value()
    
    4. Add performance monitoring methods:
       - get_performance_metrics()
       - log_performance_metrics()
       - clear_performance_caches()
    """
    pass


# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the optimizations
    optimizer = BPMPageOptimizations()
    
    # Test numeric parsing performance
    test_values = ["25", "27-Q1", "UAT-29", "PROD-15", "123.45", "no-numbers"]
    
    print("Testing optimized numeric parsing:")
    for value in test_values:
        result = optimizer._optimized_parse_numeric_value(value)
        print(f"  '{value}' -> {result}")
    
    # Show cache statistics
    cache_stats = PerformanceOptimizer.get_cache_stats()
    print(f"\nCache statistics: {cache_stats}")
    
    # Show performance metrics
    optimizer.log_performance_metrics()