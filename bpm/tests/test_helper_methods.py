"""Unit tests for BPM helper methods for data access.

This module tests the helper methods added to the BPMPage class for accessing
specific column data, environment information, metadata, column count validation,
and convenience methods for common data access patterns.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys

# Mock playwright dependencies
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.sync_api'] = MagicMock()

from bpm.bpm_page import BPMPage, BPMSearchResult, ColumnData


class TestBPMHelperMethods(unittest.TestCase):
    """Test cases for BPM helper methods for data access."""

    def setUp(self):
        """Set up test fixtures with mock page and sample data."""
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)
        
        # Create sample column data for testing
        self.sample_columns = [
            ColumnData(position=1, value="TXN001", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="25", is_numeric=True, numeric_value=25),
            ColumnData(position=3, value="PENDING", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="USD", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="100.50", is_numeric=True, numeric_value=100),
            ColumnData(position=6, value="COMPLETE", is_numeric=False, numeric_value=None)
        ]
        
        # Create sample BPMSearchResult for testing
        self.sample_result = BPMSearchResult(
            fourth_column="USD",
            last_column="COMPLETE",
            all_columns=self.sample_columns,
            second_to_last_column="100.50",
            environment="buat",
            total_columns=6,
            transaction_found=True,
            search_timestamp="2025-01-01T12:00:00"
        )

    def test_get_column_by_position_valid(self):
        """Test getting column data by valid position."""
        # Test getting first column
        column = self.bmp_page.get_column_by_position(self.sample_result, 1)
        self.assertIsNotNone(column)
        self.assertEqual(column.position, 1)
        self.assertEqual(column.value, "TXN001")
        
        # Test getting middle column
        column = self.bmp_page.get_column_by_position(self.sample_result, 3)
        self.assertIsNotNone(column)
        self.assertEqual(column.position, 3)
        self.assertEqual(column.value, "PENDING")
        
        # Test getting last column
        column = self.bmp_page.get_column_by_position(self.sample_result, 6)
        self.assertIsNotNone(column)
        self.assertEqual(column.position, 6)
        self.assertEqual(column.value, "COMPLETE")

    def test_get_column_by_position_invalid(self):
        """Test getting column data by invalid position."""
        # Test position too low
        column = self.bmp_page.get_column_by_position(self.sample_result, 0)
        self.assertIsNone(column)
        
        # Test position too high
        column = self.bmp_page.get_column_by_position(self.sample_result, 10)
        self.assertIsNone(column)
        
        # Test negative position
        column = self.bmp_page.get_column_by_position(self.sample_result, -1)
        self.assertIsNone(column)

    def test_get_column_by_position_invalid_result(self):
        """Test getting column data with invalid result object."""
        column = self.bmp_page.get_column_by_position(None, 1)
        self.assertIsNone(column)
        
        column = self.bmp_page.get_column_by_position("invalid", 1)
        self.assertIsNone(column)

    def test_get_column_value_by_position_valid(self):
        """Test getting column value by valid position."""
        value = self.bmp_page.get_column_value_by_position(self.sample_result, 2)
        self.assertEqual(value, "25")
        
        value = self.bmp_page.get_column_value_by_position(self.sample_result, 4)
        self.assertEqual(value, "USD")

    def test_get_column_value_by_position_invalid(self):
        """Test getting column value by invalid position with default."""
        # Test with default "NotFound"
        value = self.bmp_page.get_column_value_by_position(self.sample_result, 10)
        self.assertEqual(value, "NotFound")
        
        # Test with custom default
        value = self.bmp_page.get_column_value_by_position(self.sample_result, 10, "MISSING")
        self.assertEqual(value, "MISSING")

    def test_get_numeric_columns(self):
        """Test filtering columns to get only numeric ones."""
        numeric_columns = self.bmp_page.get_numeric_columns(self.sample_result)
        
        self.assertEqual(len(numeric_columns), 2)
        self.assertEqual(numeric_columns[0].position, 2)
        self.assertEqual(numeric_columns[0].numeric_value, 25)
        self.assertEqual(numeric_columns[1].position, 5)
        self.assertEqual(numeric_columns[1].numeric_value, 100)

    def test_get_numeric_columns_empty_result(self):
        """Test getting numeric columns from result with no columns."""
        empty_result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=[],
            second_to_last_column="NotFound",
            environment="unknown",
            total_columns=0,
            transaction_found=False,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        numeric_columns = self.bmp_page.get_numeric_columns(empty_result)
        self.assertEqual(len(numeric_columns), 0)

    def test_get_environment_info_buat(self):
        """Test getting environment information for BUAT environment."""
        env_info = self.bmp_page.get_environment_info(self.sample_result)
        
        self.assertEqual(env_info["environment"], "buat")
        self.assertEqual(env_info["classification"], "Business User Acceptance Testing")
        self.assertEqual(env_info["qualifying_range"], "25-29")
        self.assertEqual(env_info["description"], "Business User Acceptance Testing environment")
        self.assertEqual(env_info["numeric_column_count"], 2)
        self.assertEqual(env_info["total_columns"], 6)
        self.assertIn(25, env_info["numeric_values_found"])
        self.assertIn(100, env_info["numeric_values_found"])

    def test_get_environment_info_uat(self):
        """Test getting environment information for UAT environment."""
        # Create UAT result with numeric value outside 25-29 range
        uat_columns = [
            ColumnData(position=1, value="TXN002", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="30", is_numeric=True, numeric_value=30),
            ColumnData(position=3, value="ACTIVE", is_numeric=False, numeric_value=None)
        ]
        
        uat_result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="ACTIVE",
            all_columns=uat_columns,
            second_to_last_column="30",
            environment="uat",
            total_columns=3,
            transaction_found=True,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        env_info = self.bmp_page.get_environment_info(uat_result)
        
        self.assertEqual(env_info["environment"], "uat")
        self.assertEqual(env_info["classification"], "User Acceptance Testing")
        self.assertEqual(env_info["qualifying_range"], "Outside 25-29")
        self.assertEqual(env_info["description"], "User Acceptance Testing environment")

    def test_get_environment_info_unknown(self):
        """Test getting environment information for unknown environment."""
        # Create result with no numeric values
        unknown_columns = [
            ColumnData(position=1, value="TXN003", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="TEXT", is_numeric=False, numeric_value=None)
        ]
        
        unknown_result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="TEXT",
            all_columns=unknown_columns,
            second_to_last_column="TXN003",
            environment="unknown",
            total_columns=2,
            transaction_found=True,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        env_info = self.bmp_page.get_environment_info(unknown_result)
        
        self.assertEqual(env_info["environment"], "unknown")
        self.assertEqual(env_info["classification"], "Unknown Environment")
        self.assertEqual(env_info["qualifying_range"], "No numeric values found")
        self.assertEqual(env_info["description"], "Environment could not be determined")

    def test_validate_column_count_valid(self):
        """Test column count validation with valid counts."""
        # Test minimum only
        self.assertTrue(self.bmp_page.validate_column_count(self.sample_result, expected_min=1))
        self.assertTrue(self.bmp_page.validate_column_count(self.sample_result, expected_min=6))
        
        # Test minimum and maximum
        self.assertTrue(self.bmp_page.validate_column_count(self.sample_result, expected_min=1, expected_max=10))
        self.assertTrue(self.bmp_page.validate_column_count(self.sample_result, expected_min=6, expected_max=6))

    def test_validate_column_count_invalid(self):
        """Test column count validation with invalid counts."""
        # Test minimum too high
        self.assertFalse(self.bmp_page.validate_column_count(self.sample_result, expected_min=10))
        
        # Test maximum too low
        self.assertFalse(self.bmp_page.validate_column_count(self.sample_result, expected_min=1, expected_max=3))

    def test_has_required_columns_valid(self):
        """Test checking for required columns with valid positions."""
        # Test single required column
        self.assertTrue(self.bmp_page.has_required_columns(self.sample_result, [1]))
        self.assertTrue(self.bmp_page.has_required_columns(self.sample_result, [4]))
        
        # Test multiple required columns
        self.assertTrue(self.bmp_page.has_required_columns(self.sample_result, [1, 2, 4]))
        self.assertTrue(self.bmp_page.has_required_columns(self.sample_result, [2, 5, 6]))
        
        # Test empty requirements (should pass)
        self.assertTrue(self.bmp_page.has_required_columns(self.sample_result, []))

    def test_has_required_columns_invalid(self):
        """Test checking for required columns with invalid positions."""
        # Test position beyond available columns
        self.assertFalse(self.bmp_page.has_required_columns(self.sample_result, [10]))
        
        # Test mix of valid and invalid positions
        self.assertFalse(self.bmp_page.has_required_columns(self.sample_result, [1, 2, 10]))

    def test_has_required_columns_with_error_values(self):
        """Test checking for required columns with error values."""
        # Create result with error values
        error_columns = [
            ColumnData(position=1, value="TXN001", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="ExtractionError", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="NotFound", is_numeric=False, numeric_value=None)
        ]
        
        error_result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=error_columns,
            second_to_last_column="",
            environment="unknown",
            total_columns=4,
            transaction_found=False,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        # Position 1 should pass (has valid value)
        self.assertTrue(self.bmp_page.has_required_columns(error_result, [1]))
        
        # Positions 2, 3, 4 should fail (have error/empty values)
        self.assertFalse(self.bmp_page.has_required_columns(error_result, [2]))
        self.assertFalse(self.bmp_page.has_required_columns(error_result, [3]))
        self.assertFalse(self.bmp_page.has_required_columns(error_result, [4]))

    def test_get_column_summary(self):
        """Test getting column summary information."""
        summary = self.bmp_page.get_column_summary(self.sample_result)
        
        self.assertEqual(summary["total_columns"], 6)
        self.assertEqual(summary["numeric_columns"], 2)
        self.assertEqual(summary["empty_columns"], 0)
        self.assertEqual(summary["error_columns"], 0)
        self.assertEqual(summary["environment"], "buat")
        self.assertTrue(summary["transaction_found"])
        
        # Check key columns
        self.assertEqual(summary["key_columns"]["fourth_column"], "USD")
        self.assertEqual(summary["key_columns"]["last_column"], "COMPLETE")
        self.assertEqual(summary["key_columns"]["second_to_last_column"], "100.50")
        
        # Check numeric values
        self.assertIn(25, summary["numeric_values"])
        self.assertIn(100, summary["numeric_values"])

    def test_get_column_summary_empty_result(self):
        """Test getting column summary for empty result."""
        empty_result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=[],
            second_to_last_column="NotFound",
            environment="unknown",
            total_columns=0,
            transaction_found=False,
            search_timestamp="2025-01-01T12:00:00"
        )
        
        summary = self.bmp_page.get_column_summary(empty_result)
        
        self.assertEqual(summary["total_columns"], 0)
        self.assertEqual(summary["numeric_columns"], 0)
        self.assertEqual(summary["empty_columns"], 0)
        self.assertEqual(summary["error_columns"], 0)
        self.assertEqual(summary["environment"], "unknown")
        self.assertFalse(summary["transaction_found"])

    def test_find_columns_with_pattern(self):
        """Test finding columns that match a specific pattern."""
        # Test finding columns with "TXN" pattern
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, r"TXN\d+")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].position, 1)
        self.assertEqual(matches[0].value, "TXN001")
        
        # Test finding columns with numeric pattern
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, r"^\d+$")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].position, 2)
        self.assertEqual(matches[0].value, "25")
        
        # Test case insensitive search
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, r"complete", case_sensitive=False)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].position, 6)
        
        # Test case sensitive search (should not match)
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, r"complete", case_sensitive=True)
        self.assertEqual(len(matches), 0)

    def test_find_columns_with_pattern_no_matches(self):
        """Test finding columns with pattern that has no matches."""
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, r"NONEXISTENT")
        self.assertEqual(len(matches), 0)

    def test_find_columns_with_pattern_invalid_regex(self):
        """Test finding columns with invalid regex pattern."""
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, r"[invalid")
        self.assertEqual(len(matches), 0)

    def test_find_columns_with_pattern_empty_pattern(self):
        """Test finding columns with empty pattern."""
        matches = self.bmp_page.find_columns_with_pattern(self.sample_result, "")
        self.assertEqual(len(matches), 0)

    def test_helper_methods_with_invalid_result_types(self):
        """Test helper methods with invalid result types."""
        # Test with None
        self.assertEqual(self.bmp_page.get_numeric_columns(None), [])
        self.assertFalse(self.bmp_page.validate_column_count(None))
        self.assertFalse(self.bmp_page.has_required_columns(None, [1]))
        
        # Test with string instead of BPMSearchResult
        self.assertEqual(self.bmp_page.get_numeric_columns("invalid"), [])
        self.assertFalse(self.bmp_page.validate_column_count("invalid"))
        self.assertFalse(self.bmp_page.has_required_columns("invalid", [1]))

    @patch('bpm.bpm_page.datetime')
    def test_get_default_environment_info(self, mock_datetime):
        """Test getting default environment info structure."""
        mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T12:00:00"
        
        default_info = self.bmp_page._get_default_environment_info("test_env")
        
        self.assertEqual(default_info["environment"], "test_env")
        self.assertEqual(default_info["classification"], "Unknown Environment")
        self.assertEqual(default_info["numeric_values_found"], [])
        self.assertEqual(default_info["numeric_column_count"], 0)
        self.assertEqual(default_info["total_columns"], 0)
        self.assertEqual(default_info["detection_timestamp"], "2025-01-01T12:00:00")
        self.assertEqual(default_info["qualifying_range"], "Unknown")
        self.assertEqual(default_info["description"], "Environment information unavailable")

    def test_get_environment_classification(self):
        """Test getting human-readable environment classification."""
        self.assertEqual(self.bmp_page._get_environment_classification("buat"), "Business User Acceptance Testing")
        self.assertEqual(self.bmp_page._get_environment_classification("uat"), "User Acceptance Testing")
        self.assertEqual(self.bmp_page._get_environment_classification("unknown"), "Unknown Environment")
        self.assertEqual(self.bmp_page._get_environment_classification("invalid"), "Unknown Environment")


if __name__ == '__main__':
    unittest.main()