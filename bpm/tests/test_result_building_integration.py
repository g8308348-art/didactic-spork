"""Integration tests for result building methods with other BPMPage components.

Tests the integration between result building methods and other components
like column extraction and environment detection.
"""

import unittest
from unittest.mock import Mock, MagicMock
from bpm.bpm_page import BPMPage, ColumnData


class TestResultBuildingIntegration(unittest.TestCase):
    """Integration test cases for result building methods."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock page object
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)

    def test_full_workflow_with_buat_environment(self):
        """Test complete workflow: column extraction -> environment detection -> result building."""
        # Mock column extraction to return test data with BUAT value first
        test_columns = [
            ColumnData(position=1, value="TXN001", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="PROCESSING", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="USD", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="27-Q2", is_numeric=True, numeric_value=27),  # BUAT range (first numeric)
            ColumnData(position=5, value="500.00", is_numeric=True, numeric_value=500),
            ColumnData(position=6, value="ACTIVE", is_numeric=False, numeric_value=None)
        ]
        
        # Test environment detection (should find 27 first and return "buat")
        detected_environment = self.bmp_page._detect_environment(test_columns)
        self.assertEqual(detected_environment, "buat")
        
        # Test result building with detected environment
        result = self.bmp_page._build_enhanced_result(test_columns, detected_environment)
        
        # Verify complete result
        self.assertEqual(result.fourth_column, "27-Q2")
        self.assertEqual(result.last_column, "ACTIVE")
        self.assertEqual(result.second_to_last_column, "500.00")
        self.assertEqual(result.environment, "buat")
        self.assertEqual(result.total_columns, 6)
        self.assertTrue(result.transaction_found)
        self.assertEqual(len(result.all_columns), 6)

    def test_full_workflow_with_uat_environment(self):
        """Test complete workflow with UAT environment detection."""
        test_columns = [
            ColumnData(position=1, value="TXN002", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="15", is_numeric=True, numeric_value=15),  # UAT (outside 25-29)
            ColumnData(position=3, value="COMPLETED", is_numeric=False, numeric_value=None)
        ]
        
        # Test environment detection
        detected_environment = self.bmp_page._detect_environment(test_columns)
        self.assertEqual(detected_environment, "uat")
        
        # Test result building
        result = self.bmp_page._build_enhanced_result(test_columns, detected_environment)
        
        # Verify result
        self.assertEqual(result.fourth_column, "NotFound")  # Only 3 columns
        self.assertEqual(result.last_column, "COMPLETED")
        self.assertEqual(result.second_to_last_column, "15")
        self.assertEqual(result.environment, "uat")
        self.assertEqual(result.total_columns, 3)

    def test_full_workflow_with_unknown_environment(self):
        """Test complete workflow with unknown environment (no numeric values)."""
        test_columns = [
            ColumnData(position=1, value="TXN003", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="PENDING", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="EUR", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="WAITING", is_numeric=False, numeric_value=None)
        ]
        
        # Test environment detection
        detected_environment = self.bmp_page._detect_environment(test_columns)
        self.assertEqual(detected_environment, "unknown")
        
        # Test result building
        result = self.bmp_page._build_enhanced_result(test_columns, detected_environment)
        
        # Verify result
        self.assertEqual(result.fourth_column, "WAITING")
        self.assertEqual(result.last_column, "WAITING")
        self.assertEqual(result.second_to_last_column, "EUR")
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 4)

    def test_error_handling_integration(self):
        """Test error handling when components fail."""
        # Test with invalid column data
        invalid_columns = "not a list"
        
        # Environment detection should handle invalid input
        environment = self.bmp_page._detect_environment(invalid_columns)
        self.assertEqual(environment, "unknown")
        
        # Result building should handle invalid input
        result = self.bmp_page._build_enhanced_result(invalid_columns, environment)
        
        # Should return not found result
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertFalse(result.transaction_found)

    def test_serialization_integration(self):
        """Test that the complete workflow produces serializable results."""
        test_columns = [
            ColumnData(position=1, value="TXN004", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="28", is_numeric=True, numeric_value=28),
            ColumnData(position=3, value="FINAL", is_numeric=False, numeric_value=None)
        ]
        
        # Complete workflow
        environment = self.bmp_page._detect_environment(test_columns)
        result = self.bmp_page._build_enhanced_result(test_columns, environment)
        
        # Test serialization
        result_dict = result.to_dict()
        
        # Verify serialized structure
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict["environment"], "buat")
        self.assertEqual(result_dict["total_columns"], 3)
        self.assertTrue(result_dict["transaction_found"])
        
        # Verify column data serialization
        self.assertEqual(len(result_dict["all_columns"]), 3)
        self.assertEqual(result_dict["all_columns"][1]["value"], "28")
        self.assertTrue(result_dict["all_columns"][1]["is_numeric"])
        self.assertEqual(result_dict["all_columns"][1]["numeric_value"], 28)

    def test_edge_case_single_numeric_column(self):
        """Test edge case with single column containing numeric value."""
        test_columns = [
            ColumnData(position=1, value="26", is_numeric=True, numeric_value=26)
        ]
        
        # Complete workflow
        environment = self.bmp_page._detect_environment(test_columns)
        result = self.bmp_page._build_enhanced_result(test_columns, environment)
        
        # Verify results
        self.assertEqual(environment, "buat")
        self.assertEqual(result.fourth_column, "NotFound")  # No 4th column
        self.assertEqual(result.last_column, "26")  # Same as first column
        self.assertEqual(result.second_to_last_column, "NotFound")  # No second-to-last
        self.assertEqual(result.environment, "buat")
        self.assertEqual(result.total_columns, 1)

    def test_boundary_values_environment_detection(self):
        """Test boundary values for environment detection (25 and 29)."""
        # Test with value 25 (lower boundary of BUAT)
        columns_25 = [
            ColumnData(position=1, value="25", is_numeric=True, numeric_value=25)
        ]
        env_25 = self.bmp_page._detect_environment(columns_25)
        self.assertEqual(env_25, "buat")
        
        # Test with value 29 (upper boundary of BUAT)
        columns_29 = [
            ColumnData(position=1, value="29", is_numeric=True, numeric_value=29)
        ]
        env_29 = self.bmp_page._detect_environment(columns_29)
        self.assertEqual(env_29, "buat")
        
        # Test with value 24 (just below BUAT range)
        columns_24 = [
            ColumnData(position=1, value="24", is_numeric=True, numeric_value=24)
        ]
        env_24 = self.bmp_page._detect_environment(columns_24)
        self.assertEqual(env_24, "uat")
        
        # Test with value 30 (just above BUAT range)
        columns_30 = [
            ColumnData(position=1, value="30", is_numeric=True, numeric_value=30)
        ]
        env_30 = self.bmp_page._detect_environment(columns_30)
        self.assertEqual(env_30, "uat")


if __name__ == '__main__':
    unittest.main()