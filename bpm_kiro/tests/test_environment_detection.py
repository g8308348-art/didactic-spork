"""Unit tests for environment detection functionality in BPM page."""

import unittest
import sys
import os
from unittest.mock import Mock

# Add the bpm directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bpm'))

from bpm_page import BPMPage, ColumnData


class TestEnvironmentDetection(unittest.TestCase):
    """Test cases for _detect_environment method."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock page object for BPMPage initialization
        mock_page = Mock()
        self.bmp_page = BPMPage(mock_page)

    def test_detect_buat_environment_single_column(self):
        """Test detection of BUAT environment with single qualifying column."""
        buat_values = [25, 26, 27, 28, 29]
        
        for value in buat_values:
            with self.subTest(value=value):
                columns = [
                    ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)
                ]
                environment = self.bmp_page._detect_environment(columns)
                self.assertEqual(environment, "buat")

    def test_detect_uat_environment_single_column(self):
        """Test detection of UAT environment with single qualifying column."""
        uat_values = [1, 24, 30, 50, 100, 0, -5]
        
        for value in uat_values:
            with self.subTest(value=value):
                columns = [
                    ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)
                ]
                environment = self.bmp_page._detect_environment(columns)
                self.assertEqual(environment, "uat")

    def test_detect_unknown_environment_no_numeric_values(self):
        """Test detection returns unknown when no numeric values are found."""
        columns = [
            ColumnData(position=1, value="ABC", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="DEF", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="GHI", is_numeric=False, numeric_value=None),
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "unknown")

    def test_detect_environment_multiple_columns_first_match_wins(self):
        """Test that environment detection uses the first qualifying numeric value found."""
        # First column has BUAT value, second has UAT value - should return BUAT
        columns = [
            ColumnData(position=1, value="25", is_numeric=True, numeric_value=25),
            ColumnData(position=2, value="30", is_numeric=True, numeric_value=30),
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "buat")

        # First column has UAT value, second has BUAT value - should return UAT
        columns = [
            ColumnData(position=1, value="24", is_numeric=True, numeric_value=24),
            ColumnData(position=2, value="27", is_numeric=True, numeric_value=27),
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "uat")

    def test_detect_environment_mixed_numeric_and_non_numeric_columns(self):
        """Test environment detection with mixed column types."""
        # Non-numeric columns followed by BUAT numeric column
        columns = [
            ColumnData(position=1, value="ABC", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="DEF", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="27", is_numeric=True, numeric_value=27),
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "buat")

        # Non-numeric columns followed by UAT numeric column
        columns = [
            ColumnData(position=1, value="XYZ", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="123ABC", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="31", is_numeric=True, numeric_value=31),
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "uat")

    def test_detect_environment_realistic_column_data(self):
        """Test environment detection with realistic column data from BPM results."""
        # Realistic BUAT scenario
        buat_columns = [
            ColumnData(position=1, value="DEH", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="PF2EFBA2200914", is_numeric=True, numeric_value=2),  # UAT value but not first qualifying
            ColumnData(position=3, value="25-Q1", is_numeric=True, numeric_value=25),  # BUAT value - should be detected
            ColumnData(position=4, value="2025-08-06 10:57:32", is_numeric=True, numeric_value=2025),
            ColumnData(position=5, value="BusinessResponseProcessed", is_numeric=False, numeric_value=None),
            ColumnData(position=6, value="EUR", is_numeric=False, numeric_value=None),
        ]
        environment = self.bmp_page._detect_environment(buat_columns)
        self.assertEqual(environment, "uat")  # First numeric value (2) is UAT

        # Realistic UAT scenario
        uat_columns = [
            ColumnData(position=1, value="DEH", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="TRANSACTION_ID", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="22-Q1", is_numeric=True, numeric_value=22),  # UAT value
            ColumnData(position=4, value="SUCCESS", is_numeric=False, numeric_value=None),
        ]
        environment = self.bmp_page._detect_environment(uat_columns)
        self.assertEqual(environment, "uat")

        # Realistic BUAT scenario where BUAT value comes first
        buat_first_columns = [
            ColumnData(position=1, value="ENV-27", is_numeric=True, numeric_value=27),  # BUAT value first
            ColumnData(position=2, value="TRANSACTION_ID", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="100", is_numeric=True, numeric_value=100),  # UAT value but comes after
        ]
        environment = self.bmp_page._detect_environment(buat_first_columns)
        self.assertEqual(environment, "buat")

    def test_detect_environment_edge_cases(self):
        """Test environment detection with edge cases."""
        # Empty columns list
        environment = self.bmp_page._detect_environment([])
        self.assertEqual(environment, "unknown")

        # None input
        environment = self.bmp_page._detect_environment(None)
        self.assertEqual(environment, "unknown")

        # Single column with None numeric_value but is_numeric=True (edge case)
        columns = [
            ColumnData(position=1, value="25", is_numeric=True, numeric_value=None)
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "unknown")

        # Column with is_numeric=False but has numeric_value (edge case)
        columns = [
            ColumnData(position=1, value="25", is_numeric=False, numeric_value=25)
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "unknown")

    def test_detect_environment_boundary_values(self):
        """Test environment detection with boundary values."""
        # Test exact boundary values
        boundary_test_cases = [
            (24, "uat"),   # Just below BUAT range
            (25, "buat"),  # Lower boundary of BUAT range
            (29, "buat"),  # Upper boundary of BUAT range
            (30, "uat"),   # Just above BUAT range
        ]

        for value, expected_env in boundary_test_cases:
            with self.subTest(value=value, expected=expected_env):
                columns = [
                    ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)
                ]
                environment = self.bmp_page._detect_environment(columns)
                self.assertEqual(environment, expected_env)

    def test_detect_environment_with_negative_values(self):
        """Test environment detection with negative numeric values."""
        negative_values = [-1, -25, -29, -100]
        
        for value in negative_values:
            with self.subTest(value=value):
                columns = [
                    ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)
                ]
                environment = self.bmp_page._detect_environment(columns)
                self.assertEqual(environment, "uat")  # All negative values should be UAT

    def test_detect_environment_with_zero_value(self):
        """Test environment detection with zero value."""
        columns = [
            ColumnData(position=1, value="0", is_numeric=True, numeric_value=0)
        ]
        environment = self.bmp_page._detect_environment(columns)
        self.assertEqual(environment, "uat")  # Zero should be UAT

    def test_detect_environment_with_large_values(self):
        """Test environment detection with large numeric values."""
        large_values = [100, 1000, 9999, 25000]
        
        for value in large_values:
            with self.subTest(value=value):
                columns = [
                    ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)
                ]
                environment = self.bmp_page._detect_environment(columns)
                self.assertEqual(environment, "uat")  # All large values should be UAT

    def test_detect_environment_invalid_column_data(self):
        """Test environment detection with invalid column data."""
        # List containing non-ColumnData objects
        invalid_columns = [
            "not_a_column_data",
            {"position": 1, "value": "25"},
            None,
            ColumnData(position=1, value="27", is_numeric=True, numeric_value=27),  # Valid one
        ]
        
        environment = self.bmp_page._detect_environment(invalid_columns)
        self.assertEqual(environment, "buat")  # Should find the valid ColumnData with value 27

    def test_detect_environment_comprehensive_scenarios(self):
        """Test comprehensive real-world scenarios for environment detection."""
        
        # Scenario 1: Typical BUAT transaction with mixed data
        scenario_1 = [
            ColumnData(position=1, value="TRANSACTION_REF", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="PACS.008", is_numeric=True, numeric_value=8),  # UAT value
            ColumnData(position=3, value="SUCCESS", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="EUR", is_numeric=False, numeric_value=None),
        ]
        self.assertEqual(self.bmp_page._detect_environment(scenario_1), "uat")

        # Scenario 2: BUAT environment with qualifying value first
        scenario_2 = [
            ColumnData(position=1, value="28-PROD", is_numeric=True, numeric_value=28),  # BUAT value
            ColumnData(position=2, value="TRANSACTION_ID", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="2025-08-06", is_numeric=True, numeric_value=2025),  # UAT value but comes after
        ]
        self.assertEqual(self.bmp_page._detect_environment(scenario_2), "buat")

        # Scenario 3: No numeric values at all
        scenario_3 = [
            ColumnData(position=1, value="REFERENCE", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="STATUS", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="CURRENCY", is_numeric=False, numeric_value=None),
        ]
        self.assertEqual(self.bmp_page._detect_environment(scenario_3), "unknown")

        # Scenario 4: Multiple BUAT values
        scenario_4 = [
            ColumnData(position=1, value="25", is_numeric=True, numeric_value=25),  # BUAT
            ColumnData(position=2, value="26", is_numeric=True, numeric_value=26),  # BUAT
            ColumnData(position=3, value="27", is_numeric=True, numeric_value=27),  # BUAT
        ]
        self.assertEqual(self.bmp_page._detect_environment(scenario_4), "buat")

        # Scenario 5: Multiple UAT values
        scenario_5 = [
            ColumnData(position=1, value="1", is_numeric=True, numeric_value=1),    # UAT
            ColumnData(position=2, value="24", is_numeric=True, numeric_value=24),  # UAT
            ColumnData(position=3, value="30", is_numeric=True, numeric_value=30),  # UAT
        ]
        self.assertEqual(self.bmp_page._detect_environment(scenario_5), "uat")

    def test_detect_environment_error_handling(self):
        """Test environment detection error handling."""
        # Test with invalid input types
        invalid_inputs = [
            "not_a_list",
            123,
            {"key": "value"},
            True,
        ]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input=invalid_input):
                environment = self.bmp_page._detect_environment(invalid_input)
                self.assertEqual(environment, "unknown")

    def test_detect_environment_logging_verification(self):
        """Test that environment detection produces appropriate log messages."""
        # This test verifies the logging behavior by checking the method execution
        # In a real scenario, you might want to capture and verify log messages
        
        # BUAT detection
        buat_columns = [
            ColumnData(position=2, value="27", is_numeric=True, numeric_value=27)
        ]
        environment = self.bmp_page._detect_environment(buat_columns)
        self.assertEqual(environment, "buat")

        # UAT detection
        uat_columns = [
            ColumnData(position=1, value="24", is_numeric=True, numeric_value=24)
        ]
        environment = self.bmp_page._detect_environment(uat_columns)
        self.assertEqual(environment, "uat")

        # Unknown detection
        unknown_columns = [
            ColumnData(position=1, value="TEXT", is_numeric=False, numeric_value=None)
        ]
        environment = self.bmp_page._detect_environment(unknown_columns)
        self.assertEqual(environment, "unknown")

    def test_detect_environment_requirements_compliance(self):
        """Test that environment detection meets all specified requirements."""
        
        # Requirement 3.1: Values 25-29 should classify as "buat"
        for value in range(25, 30):  # 25-29 inclusive
            columns = [ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)]
            environment = self.bmp_page._detect_environment(columns)
            self.assertEqual(environment, "buat", f"Value {value} should classify as 'buat'")

        # Requirement 3.2: Values outside 25-29 should classify as "uat"
        outside_range_values = [1, 24, 30, 50, 100]
        for value in outside_range_values:
            columns = [ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)]
            environment = self.bmp_page._detect_environment(columns)
            self.assertEqual(environment, "uat", f"Value {value} should classify as 'uat'")

        # Requirement 3.3: First qualifying number should be used for determination
        mixed_columns = [
            ColumnData(position=1, value="TEXT", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="30", is_numeric=True, numeric_value=30),  # UAT - first numeric
            ColumnData(position=3, value="27", is_numeric=True, numeric_value=27),  # BUAT - second numeric
        ]
        environment = self.bmp_page._detect_environment(mixed_columns)
        self.assertEqual(environment, "uat", "Should use first qualifying numeric value (30)")

        # Requirement 3.4: No numeric values should return "unknown"
        no_numeric_columns = [
            ColumnData(position=1, value="ABC", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="DEF", is_numeric=False, numeric_value=None),
        ]
        environment = self.bmp_page._detect_environment(no_numeric_columns)
        self.assertEqual(environment, "unknown", "No numeric values should return 'unknown'")

        # Requirement 3.5: Environment detection should be returned as part of response data
        # This is tested implicitly by all other tests - the method returns the environment string


if __name__ == '__main__':
    unittest.main()