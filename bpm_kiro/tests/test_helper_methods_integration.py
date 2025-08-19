"""Integration tests for BPM helper methods with existing functionality.

This module tests that the helper methods integrate properly with the existing
BPM search functionality and data structures.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys

# Mock playwright dependencies
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.sync_api'] = MagicMock()

from bpm.bpm_page import BPMPage, BPMSearchResult, ColumnData


class TestBPMHelperMethodsIntegration(unittest.TestCase):
    """Integration test cases for BPM helper methods."""

    def setUp(self):
        """Set up test fixtures with mock page."""
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)

    def test_helper_methods_with_enhanced_search_result(self):
        """Test helper methods work with results from enhanced search methods."""
        # Create a realistic search result that would come from enhanced search
        columns = [
            ColumnData(position=1, value="REF123456", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="27-Q1", is_numeric=True, numeric_value=27),
            ColumnData(position=3, value="PROCESSING", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="EUR", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="1500.75", is_numeric=True, numeric_value=1500),
            ColumnData(position=6, value="COMPLETED", is_numeric=False, numeric_value=None)
        ]
        
        enhanced_result = BPMSearchResult(
            fourth_column="EUR",
            last_column="COMPLETED",
            all_columns=columns,
            second_to_last_column="1500.75",
            environment="buat",
            total_columns=6,
            transaction_found=True,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        # Test that all helper methods work with this result
        
        # Test column access
        ref_column = self.bmp_page.get_column_by_position(enhanced_result, 1)
        self.assertEqual(ref_column.value, "REF123456")
        
        currency_value = self.bmp_page.get_column_value_by_position(enhanced_result, 4)
        self.assertEqual(currency_value, "EUR")
        
        # Test numeric column filtering
        numeric_columns = self.bmp_page.get_numeric_columns(enhanced_result)
        self.assertEqual(len(numeric_columns), 2)
        self.assertEqual(numeric_columns[0].numeric_value, 27)
        self.assertEqual(numeric_columns[1].numeric_value, 1500)
        
        # Test environment information
        env_info = self.bmp_page.get_environment_info(enhanced_result)
        self.assertEqual(env_info["environment"], "buat")
        self.assertEqual(env_info["numeric_column_count"], 2)
        self.assertIn(27, env_info["numeric_values_found"])
        
        # Test validation methods
        self.assertTrue(self.bmp_page.validate_column_count(enhanced_result, expected_min=4))
        self.assertTrue(self.bmp_page.has_required_columns(enhanced_result, [1, 4, 6]))
        
        # Test summary generation
        summary = self.bmp_page.get_column_summary(enhanced_result)
        self.assertEqual(summary["total_columns"], 6)
        self.assertEqual(summary["numeric_columns"], 2)
        self.assertEqual(summary["environment"], "buat")
        
        # Test pattern matching
        ref_matches = self.bmp_page.find_columns_with_pattern(enhanced_result, r"REF\d+")
        self.assertEqual(len(ref_matches), 1)
        self.assertEqual(ref_matches[0].position, 1)

    def test_helper_methods_with_minimal_result(self):
        """Test helper methods work with minimal search results."""
        # Create minimal result (like what might come from error cases)
        minimal_columns = [
            ColumnData(position=1, value="TXN001", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="NotFound", is_numeric=False, numeric_value=None)
        ]
        
        minimal_result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=minimal_columns,
            second_to_last_column="TXN001",
            environment="unknown",
            total_columns=2,
            transaction_found=False,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        # Test helper methods handle minimal data gracefully
        
        # Column access should work for available columns
        first_column = self.bmp_page.get_column_by_position(minimal_result, 1)
        self.assertEqual(first_column.value, "TXN001")
        
        # Should return None/default for unavailable columns
        missing_column = self.bmp_page.get_column_by_position(minimal_result, 4)
        self.assertIsNone(missing_column)
        
        missing_value = self.bmp_page.get_column_value_by_position(minimal_result, 4)
        self.assertEqual(missing_value, "NotFound")
        
        # Numeric filtering should return empty list
        numeric_columns = self.bmp_page.get_numeric_columns(minimal_result)
        self.assertEqual(len(numeric_columns), 0)
        
        # Environment info should handle unknown environment
        env_info = self.bmp_page.get_environment_info(minimal_result)
        self.assertEqual(env_info["environment"], "unknown")
        self.assertEqual(env_info["numeric_column_count"], 0)
        
        # Validation should work appropriately
        self.assertTrue(self.bmp_page.validate_column_count(minimal_result, expected_min=1))
        self.assertFalse(self.bmp_page.validate_column_count(minimal_result, expected_min=5))
        
        # Required columns check should handle missing columns
        self.assertTrue(self.bmp_page.has_required_columns(minimal_result, [1]))
        self.assertFalse(self.bmp_page.has_required_columns(minimal_result, [2]))  # "NotFound" value

    def test_helper_methods_common_usage_patterns(self):
        """Test common usage patterns for the helper methods."""
        # Create a typical search result
        typical_columns = [
            ColumnData(position=1, value="TXN789", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="28", is_numeric=True, numeric_value=28),
            ColumnData(position=3, value="SWIFT", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="USD", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="2500.00", is_numeric=True, numeric_value=2500),
            ColumnData(position=6, value="SETTLED", is_numeric=False, numeric_value=None)
        ]
        
        typical_result = BPMSearchResult(
            fourth_column="USD",
            last_column="SETTLED",
            all_columns=typical_columns,
            second_to_last_column="2500.00",
            environment="buat",
            total_columns=6,
            transaction_found=True,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        # Common pattern 1: Check if result has minimum required data
        has_basic_data = (
            self.bmp_page.validate_column_count(typical_result, expected_min=4) and
            self.bmp_page.has_required_columns(typical_result, [1, 4, 6])
        )
        self.assertTrue(has_basic_data)
        
        # Common pattern 2: Get key transaction information
        transaction_ref = self.bmp_page.get_column_value_by_position(typical_result, 1)
        currency = self.bmp_page.get_column_value_by_position(typical_result, 4)
        status = self.bmp_page.get_column_value_by_position(typical_result, 6)
        
        self.assertEqual(transaction_ref, "TXN789")
        self.assertEqual(currency, "USD")
        self.assertEqual(status, "SETTLED")
        
        # Common pattern 3: Analyze environment and numeric data
        env_info = self.bmp_page.get_environment_info(typical_result)
        numeric_columns = self.bmp_page.get_numeric_columns(typical_result)
        
        self.assertEqual(env_info["environment"], "buat")
        self.assertEqual(len(numeric_columns), 2)
        
        # Common pattern 4: Generate summary for logging/debugging
        summary = self.bmp_page.get_column_summary(typical_result)
        
        self.assertIn("total_columns", summary)
        self.assertIn("numeric_columns", summary)
        self.assertIn("environment", summary)
        self.assertIn("key_columns", summary)
        
        # Common pattern 5: Search for specific data patterns
        amount_columns = self.bmp_page.find_columns_with_pattern(typical_result, r"\d+\.\d+")
        self.assertEqual(len(amount_columns), 1)
        self.assertEqual(amount_columns[0].value, "2500.00")

    def test_backward_compatibility_with_helper_methods(self):
        """Test that helper methods work with data from backward compatible methods."""
        # Simulate what would happen when using helper methods with results
        # that maintain backward compatibility
        
        # Create result that represents backward compatible data
        compat_columns = [
            ColumnData(position=1, value="OLD001", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="GBP", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="", is_numeric=False, numeric_value=None),
            ColumnData(position=6, value="PROCESSED", is_numeric=False, numeric_value=None)
        ]
        
        compat_result = BPMSearchResult(
            fourth_column="GBP",  # Traditional 4th column
            last_column="PROCESSED",  # Traditional last column
            all_columns=compat_columns,
            second_to_last_column="",  # May be empty in older data
            environment="unknown",  # May not be detectable
            total_columns=6,
            transaction_found=True,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        # Test that helper methods handle backward compatible data gracefully
        
        # Should still be able to access the key columns
        fourth_col = self.bmp_page.get_column_value_by_position(compat_result, 4)
        last_col = self.bmp_page.get_column_value_by_position(compat_result, 6)
        
        self.assertEqual(fourth_col, "GBP")
        self.assertEqual(last_col, "PROCESSED")
        
        # Should handle empty columns appropriately
        empty_col = self.bmp_page.get_column_value_by_position(compat_result, 2)
        self.assertEqual(empty_col, "")
        
        # Should not find numeric columns in this case
        numeric_columns = self.bmp_page.get_numeric_columns(compat_result)
        self.assertEqual(len(numeric_columns), 0)
        
        # Should still validate column structure
        self.assertTrue(self.bmp_page.validate_column_count(compat_result, expected_min=4))
        
        # Should handle required columns check with empty values
        self.assertTrue(self.bmp_page.has_required_columns(compat_result, [1, 4, 6]))
        self.assertFalse(self.bmp_page.has_required_columns(compat_result, [2]))  # Empty value
        
        # Summary should reflect the data state
        summary = self.bmp_page.get_column_summary(compat_result)
        self.assertEqual(summary["numeric_columns"], 0)
        self.assertEqual(summary["empty_columns"], 3)  # Positions 2, 3, 5 are empty
        self.assertEqual(summary["environment"], "unknown")


if __name__ == '__main__':
    unittest.main()