"""Unit tests for enhanced result building methods in BPMPage.

Tests the _build_enhanced_result and _build_not_found_result methods
with various column configurations and edge cases.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from bpm.bpm_page import BPMPage, ColumnData, BPMSearchResult


class TestResultBuilding(unittest.TestCase):
    """Test cases for enhanced result building methods."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock page object
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)

    def test_build_enhanced_result_standard_case(self):
        """Test building enhanced result with standard column configuration."""
        # Create test columns (6 columns with mixed data)
        columns = [
            ColumnData(position=1, value="TXN123", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="PENDING", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="USD", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="1000.00", is_numeric=True, numeric_value=1000),
            ColumnData(position=5, value="25-Q1", is_numeric=True, numeric_value=25),
            ColumnData(position=6, value="COMPLETED", is_numeric=False, numeric_value=None)
        ]
        
        environment = "buat"
        
        # Test the method
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Verify the result structure
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "1000.00")
        self.assertEqual(result.last_column, "COMPLETED")
        self.assertEqual(result.second_to_last_column, "25-Q1")
        self.assertEqual(result.environment, "buat")
        self.assertEqual(result.total_columns, 6)
        self.assertTrue(result.transaction_found)
        self.assertEqual(len(result.all_columns), 6)
        
        # Verify timestamp is set
        self.assertIsNotNone(result.search_timestamp)
        # Verify timestamp is in ISO format
        datetime.fromisoformat(result.search_timestamp)

    def test_build_enhanced_result_minimal_columns(self):
        """Test building enhanced result with minimal column count (2 columns)."""
        columns = [
            ColumnData(position=1, value="TXN456", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="FAILED", is_numeric=False, numeric_value=None)
        ]
        
        environment = "unknown"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # With only 2 columns, 4th column should be "NotFound"
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "FAILED")  # Last column (position 2)
        self.assertEqual(result.second_to_last_column, "TXN456")  # Second-to-last (position 1)
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 2)
        self.assertTrue(result.transaction_found)

    def test_build_enhanced_result_single_column(self):
        """Test building enhanced result with only one column."""
        columns = [
            ColumnData(position=1, value="SINGLE", is_numeric=False, numeric_value=None)
        ]
        
        environment = "uat"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # With only 1 column
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "SINGLE")  # Last column (position 1)
        self.assertEqual(result.second_to_last_column, "NotFound")  # No second-to-last
        self.assertEqual(result.environment, "uat")
        self.assertEqual(result.total_columns, 1)
        self.assertTrue(result.transaction_found)

    def test_build_enhanced_result_many_columns(self):
        """Test building enhanced result with many columns (10+ columns)."""
        columns = []
        for i in range(12):
            columns.append(
                ColumnData(
                    position=i + 1,
                    value=f"COL{i+1}",
                    is_numeric=(i % 3 == 0),  # Every 3rd column is numeric
                    numeric_value=(i + 1) if (i % 3 == 0) else None
                )
            )
        
        environment = "buat"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Verify specific column extraction
        self.assertEqual(result.fourth_column, "COL4")  # 4th column
        self.assertEqual(result.last_column, "COL12")  # Last column
        self.assertEqual(result.second_to_last_column, "COL11")  # Second-to-last
        self.assertEqual(result.total_columns, 12)
        self.assertEqual(len(result.all_columns), 12)

    def test_build_enhanced_result_empty_columns(self):
        """Test building enhanced result with empty column list."""
        columns = []
        environment = "unknown"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Should return a not found result
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.second_to_last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 0)
        self.assertFalse(result.transaction_found)
        self.assertEqual(len(result.all_columns), 0)

    def test_build_enhanced_result_none_columns(self):
        """Test building enhanced result with None columns."""
        columns = None
        environment = "unknown"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Should return a not found result
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.second_to_last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 0)
        self.assertFalse(result.transaction_found)

    def test_build_enhanced_result_with_empty_values(self):
        """Test building enhanced result with columns containing empty values."""
        columns = [
            ColumnData(position=1, value="", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="   ", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="VALID", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="LAST", is_numeric=False, numeric_value=None)
        ]
        
        environment = "uat"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Empty values should be preserved
        self.assertEqual(result.fourth_column, "")  # 4th column is empty
        self.assertEqual(result.last_column, "LAST")
        self.assertEqual(result.second_to_last_column, "")  # 4th column (second-to-last)
        self.assertEqual(result.total_columns, 5)

    @patch('bpm.bpm_page.datetime')
    def test_build_enhanced_result_timestamp_error(self, mock_datetime):
        """Test building enhanced result when timestamp generation fails."""
        # Mock datetime to raise an exception
        mock_datetime.now.side_effect = Exception("Timestamp error")
        
        columns = [
            ColumnData(position=1, value="TEST", is_numeric=False, numeric_value=None)
        ]
        environment = "unknown"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Should still return a not found result as fallback
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertFalse(result.transaction_found)

    def test_build_not_found_result_standard(self):
        """Test building not found result structure."""
        result = self.bmp_page._build_not_found_result()
        
        # Verify all fields are set to appropriate "not found" values
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.second_to_last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 0)
        self.assertFalse(result.transaction_found)
        self.assertEqual(len(result.all_columns), 0)
        
        # Verify timestamp is set
        self.assertIsNotNone(result.search_timestamp)
        # Verify timestamp is in ISO format
        datetime.fromisoformat(result.search_timestamp)

    @patch('bpm.bpm_page.datetime')
    def test_build_not_found_result_timestamp_error(self, mock_datetime):
        """Test building not found result when timestamp generation fails."""
        # Mock datetime to raise an exception
        mock_datetime.now.side_effect = Exception("Timestamp error")
        
        result = self.bmp_page._build_not_found_result()
        
        # Should still return a valid result with "unknown" timestamp
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.second_to_last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 0)
        self.assertFalse(result.transaction_found)
        self.assertEqual(result.search_timestamp, "unknown")

    def test_build_enhanced_result_column_data_validation(self):
        """Test that result building preserves all column data correctly."""
        columns = [
            ColumnData(position=1, value="ABC123", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="27", is_numeric=True, numeric_value=27),
            ColumnData(position=3, value="TEST-DATA", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="42.5", is_numeric=True, numeric_value=42)
        ]
        
        environment = "buat"
        
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Verify all column data is preserved
        self.assertEqual(len(result.all_columns), 4)
        
        # Check each column is preserved correctly
        for i, original_col in enumerate(columns):
            result_col = result.all_columns[i]
            self.assertEqual(result_col.position, original_col.position)
            self.assertEqual(result_col.value, original_col.value)
            self.assertEqual(result_col.is_numeric, original_col.is_numeric)
            self.assertEqual(result_col.numeric_value, original_col.numeric_value)

    def test_build_enhanced_result_environment_preservation(self):
        """Test that environment classification is preserved correctly."""
        columns = [
            ColumnData(position=1, value="TEST", is_numeric=False, numeric_value=None)
        ]
        
        # Test each environment type
        for env in ["buat", "uat", "unknown"]:
            result = self.bmp_page._build_enhanced_result(columns, env)
            self.assertEqual(result.environment, env)

    def test_to_dict_serialization(self):
        """Test that the result can be serialized to dictionary correctly."""
        columns = [
            ColumnData(position=1, value="TXN789", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="25", is_numeric=True, numeric_value=25)
        ]
        
        environment = "buat"
        result = self.bmp_page._build_enhanced_result(columns, environment)
        
        # Test dictionary conversion
        result_dict = result.to_dict()
        
        # Verify dictionary structure
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict["fourth_column"], "NotFound")
        self.assertEqual(result_dict["last_column"], "25")
        self.assertEqual(result_dict["second_to_last_column"], "TXN789")
        self.assertEqual(result_dict["environment"], "buat")
        self.assertEqual(result_dict["total_columns"], 2)
        self.assertTrue(result_dict["transaction_found"])
        
        # Verify all_columns serialization
        self.assertIsInstance(result_dict["all_columns"], list)
        self.assertEqual(len(result_dict["all_columns"]), 2)
        
        # Check first column serialization
        col1_dict = result_dict["all_columns"][0]
        self.assertEqual(col1_dict["position"], 1)
        self.assertEqual(col1_dict["value"], "TXN789")
        self.assertFalse(col1_dict["is_numeric"])
        self.assertIsNone(col1_dict["numeric_value"])


if __name__ == '__main__':
    # Run the tests
    unittest.main()