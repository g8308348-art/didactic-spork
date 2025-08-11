"""Performance optimizations for BMP data enhancement.

This module contains performance optimization classes and utilities
for improving the efficiency of column extraction, environment detection,
and numeric parsing operations.
"""

import logging
import re
from functools import lru_cache
from typing import List, Tuple, Optional, Dict, Any


class PerformanceOptimizer:
    """Performance optimization utilities for BMP data extraction."""
    
    # Cache for numeric parsing results to avoid repeated regex operations
    _numeric_parse_cache = {}
    
    # Cache for environment detection results
    _environment_cache = {}
    
    # Maximum cache sizes to prevent memory issues
    MAX_NUMERIC_CACHE_SIZE = 1000
    MAX_ENVIRONMENT_CACHE_SIZE = 500
    
    @classmethod
    def clear_caches(cls):
        """Clear all performance caches."""
        cls._numeric_parse_cache.clear()
        cls._environment_cache.clear()
        logging.debug("Performance caches cleared")
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get statistics about cache usage."""
        return {
            "numeric_cache_size": len(cls._numeric_parse_cache),
            "environment_cache_size": len(cls._environment_cache),
            "numeric_cache_max": cls.MAX_NUMERIC_CACHE_SIZE,
            "environment_cache_max": cls.MAX_ENVIRONMENT_CACHE_SIZE
        }
    
    @classmethod
    def _manage_cache_size(cls, cache_dict: dict, max_size: int):
        """Manage cache size by removing oldest entries when limit is reached."""
        if len(cache_dict) >= max_size:
            # Remove oldest 20% of entries to make room
            items_to_remove = max_size // 5
            keys_to_remove = list(cache_dict.keys())[:items_to_remove]
            for key in keys_to_remove:
                cache_dict.pop(key, None)
            logging.debug(f"Cache size managed: removed {items_to_remove} entries")


class BatchTextExtractor:
    """Optimized batch text extraction to minimize DOM queries."""
    
    @staticmethod
    def extract_all_cell_texts(parent_row) -> List[str]:
        """Extract text from all cells in a single batch operation.
        
        This method optimizes DOM queries by getting all cell texts in one operation
        rather than making individual queries for each cell.
        
        Args:
            parent_row: Playwright locator for the parent row element
            
        Returns:
            List[str]: List of text values from all cells in the row
        """
        try:
            if not parent_row:
                logging.warning("No parent row provided for batch text extraction")
                return []
            
            # Get all cells in a single locator operation
            all_cells = parent_row.locator("div.tcell")
            cell_count = all_cells.count()
            
            if cell_count == 0:
                logging.debug("No cells found for batch extraction")
                return []
            
            # Batch extract all text values using evaluate to minimize DOM queries
            cell_texts = all_cells.evaluate_all("""
                (cells) => {
                    return cells.map(cell => {
                        try {
                            return cell.innerText ? cell.innerText.trim() : '';
                        } catch (e) {
                            return '';
                        }
                    });
                }
            """)
            
            logging.debug(f"Batch extracted {len(cell_texts)} cell texts in single operation")
            return cell_texts
            
        except Exception as e:
            logging.error(f"Error in batch text extraction: {e}")
            # Fallback to individual extraction if batch fails
            return BatchTextExtractor._fallback_individual_extraction(parent_row)
    
    @staticmethod
    def _fallback_individual_extraction(parent_row) -> List[str]:
        """Fallback method for individual cell text extraction."""
        try:
            cell_texts = []
            all_cells = parent_row.locator("div.tcell")
            cell_count = all_cells.count()
            
            for i in range(cell_count):
                try:
                    cell_text = all_cells.nth(i).inner_text().strip()
                    cell_texts.append(cell_text)
                except Exception as cell_error:
                    logging.warning(f"Failed to extract text from cell {i+1}: {cell_error}")
                    cell_texts.append("")
            
            logging.debug(f"Fallback extraction completed for {len(cell_texts)} cells")
            return cell_texts
            
        except Exception as e:
            logging.error(f"Fallback extraction failed: {e}")
            return []


class OptimizedNumericParser:
    """Optimized numeric parsing with caching for common values."""
    
    # Pre-compiled regex patterns for better performance
    _PURE_INTEGER_PATTERN = re.compile(r'^-?\d+$')
    _DECIMAL_PATTERN = re.compile(r'^-?\d+\.\d+$')
    _NUMERIC_EXTRACTION_PATTERN = re.compile(r'\b(\d+)\b')
    
    @classmethod
    def parse_numeric_value_cached(cls, text: str) -> Tuple[bool, Optional[int]]:
        """Parse text to extract numeric value with caching for performance.
        
        This method uses caching to avoid repeated parsing of common values,
        significantly improving performance for repeated searches.
        
        Args:
            text: The text string to parse for numeric values
            
        Returns:
            Tuple of (is_numeric: bool, numeric_value: Optional[int])
        """
        if not text or not isinstance(text, str):
            return False, None
        
        # Check cache first
        cache_key = text.strip()
        if cache_key in PerformanceOptimizer._numeric_parse_cache:
            cached_result = PerformanceOptimizer._numeric_parse_cache[cache_key]
            logging.debug(f"Cache hit for numeric parsing: '{cache_key}' -> {cached_result}")
            return cached_result
        
        # Parse the value
        result = cls._parse_numeric_value_optimized(cache_key)
        
        # Cache the result
        PerformanceOptimizer._manage_cache_size(
            PerformanceOptimizer._numeric_parse_cache, 
            PerformanceOptimizer.MAX_NUMERIC_CACHE_SIZE
        )
        PerformanceOptimizer._numeric_parse_cache[cache_key] = result
        
        logging.debug(f"Cached numeric parsing result: '{cache_key}' -> {result}")
        return result
    
    @classmethod
    def _parse_numeric_value_optimized(cls, text: str) -> Tuple[bool, Optional[int]]:
        """Optimized numeric parsing using pre-compiled regex patterns."""
        try:
            if not text:
                return False, None
            
            # Fast path for pure integers
            if cls._PURE_INTEGER_PATTERN.match(text):
                return True, int(text)
            
            # Fast path for decimal numbers (extract integer part)
            decimal_match = cls._DECIMAL_PATTERN.match(text)
            if decimal_match:
                return True, int(float(text))
            
            # Extract first numeric value from mixed text
            numeric_match = cls._NUMERIC_EXTRACTION_PATTERN.search(text)
            if numeric_match:
                numeric_value = int(numeric_match.group(1))
                logging.debug(f"Extracted numeric value {numeric_value} from text '{text}'")
                return True, numeric_value
            
            # No numeric value found
            return False, None
            
        except (ValueError, AttributeError, TypeError) as e:
            logging.debug(f"Error parsing numeric value from text '{text}': {e}")
            return False, None


class OptimizedEnvironmentDetector:
    """Optimized environment detection with caching."""
    
    # Pre-defined environment ranges for fast lookup
    BUAT_RANGE = frozenset(range(25, 30))  # 25-29 inclusive
    
    @classmethod
    def detect_environment_cached(cls, column_data_list) -> str:
        """Detect environment with caching for repeated calls.
        
        Args:
            column_data_list: List of ColumnData objects or list of numeric values
            
        Returns:
            str: Environment classification ("buat", "uat", or "unknown")
        """
        # Create cache key from numeric values
        numeric_values = cls._extract_numeric_values(column_data_list)
        cache_key = tuple(sorted(numeric_values)) if numeric_values else ()
        
        # Check cache first
        if cache_key in PerformanceOptimizer._environment_cache:
            cached_result = PerformanceOptimizer._environment_cache[cache_key]
            logging.debug(f"Cache hit for environment detection: {cache_key} -> {cached_result}")
            return cached_result
        
        # Detect environment
        result = cls._detect_environment_optimized(numeric_values)
        
        # Cache the result
        PerformanceOptimizer._manage_cache_size(
            PerformanceOptimizer._environment_cache,
            PerformanceOptimizer.MAX_ENVIRONMENT_CACHE_SIZE
        )
        PerformanceOptimizer._environment_cache[cache_key] = result
        
        logging.debug(f"Cached environment detection result: {cache_key} -> {result}")
        return result
    
    @classmethod
    def _extract_numeric_values(cls, column_data_list) -> List[int]:
        """Extract numeric values from column data or value list."""
        numeric_values = []
        
        if not column_data_list:
            return numeric_values
        
        for item in column_data_list:
            # Handle ColumnData objects
            if hasattr(item, 'is_numeric') and hasattr(item, 'numeric_value'):
                if item.is_numeric and item.numeric_value is not None:
                    numeric_values.append(item.numeric_value)
            # Handle direct numeric values
            elif isinstance(item, (int, float)):
                numeric_values.append(int(item))
        
        return numeric_values
    
    @classmethod
    def _detect_environment_optimized(cls, numeric_values: List[int]) -> str:
        """Optimized environment detection using set operations."""
        if not numeric_values:
            return "unknown"
        
        # Use set intersection for fast range checking
        numeric_set = set(numeric_values)
        
        # Check for BUAT range first (more specific)
        if numeric_set & cls.BUAT_RANGE:
            return "buat"
        
        # Any other numeric values indicate UAT
        return "uat"


class PerformanceProfiler:
    """Performance profiling utilities for optimization validation."""
    
    def __init__(self):
        self.operation_times = {}
        self.operation_counts = {}
    
    def start_operation(self, operation_name: str):
        """Start timing an operation."""
        import time
        self.operation_times[operation_name] = time.perf_counter()
    
    def end_operation(self, operation_name: str):
        """End timing an operation and record the duration."""
        import time
        if operation_name in self.operation_times:
            duration = time.perf_counter() - self.operation_times[operation_name]
            
            # Track operation counts and cumulative time
            if operation_name not in self.operation_counts:
                self.operation_counts[operation_name] = {"count": 0, "total_time": 0.0}
            
            self.operation_counts[operation_name]["count"] += 1
            self.operation_counts[operation_name]["total_time"] += duration
            
            logging.debug(f"Operation '{operation_name}' completed in {duration:.4f}s")
            return duration
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all recorded performance metrics."""
        summary = {}
        
        for operation, stats in self.operation_counts.items():
            count = stats["count"]
            total_time = stats["total_time"]
            avg_time = total_time / count if count > 0 else 0
            
            summary[operation] = {
                "count": count,
                "total_time": total_time,
                "average_time": avg_time,
                "operations_per_second": count / total_time if total_time > 0 else 0
            }
        
        return summary
    
    def log_performance_summary(self):
        """Log a formatted performance summary."""
        summary = self.get_performance_summary()
        
        logging.info("=== Performance Summary ===")
        for operation, stats in summary.items():
            logging.info(f"{operation}:")
            logging.info(f"  Count: {stats['count']}")
            logging.info(f"  Total Time: {stats['total_time']:.4f}s")
            logging.info(f"  Average Time: {stats['average_time']:.4f}s")
            logging.info(f"  Ops/Second: {stats['operations_per_second']:.2f}")
        
        # Log cache statistics
        cache_stats = PerformanceOptimizer.get_cache_stats()
        logging.info("=== Cache Statistics ===")
        for stat_name, value in cache_stats.items():
            logging.info(f"{stat_name}: {value}")