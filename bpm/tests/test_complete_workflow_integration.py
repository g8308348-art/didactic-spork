"""Integration tests for complete BMP data enhancement workflow.

This module provides comprehensive integration tests that mock Playwright page interactions
and test the complete search flow from number lookup to enhanced result, verifying all
data fields are populated correctly in realistic scenarios and testing error handling
with various table structure edge cases.

Requirements covered:
- 1.1: Return data from all columns in result row
- 1.2: Return structured format preserving column order  
- 2.1: Extract and return second-to-last column value
- 3.5: Return detected environment as part of response data
- 4.1: Provide structured response with all columns, environment detection, and backward-compatible fields
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import logging
import sys
import os
from datetime import datetime

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from bpm.bpm_page import BPMPage, BPMSearchResult, ColumnData


class TestCompleteWorkflowIntegration(unittest.TestCase):
    """Integration test cases for complete BMP data enhancement workflow."""

    def setUp(self):
        """Set up test fixtures with comprehensive mocking."""
        # Mock the Playwright page object with all required methods
        self.mock_page = Mock()
        self.mock_page.wait_for_timeout = Mock()
        self.mock_page.wait_for_load_state = Mock()
        self.mock_page.locator = Mock()
        
        # Create BPMPage instance
        self.bmp_page = BPMPage(self.mock_page)
        
        # Set up logging to capture test output
        logging.basicConfig(level=logging.INFO)
        
        # Mock the wait_for_page_to_load method
        self.bmp_page.wait_for_page_to_load = Mock()
    
    def _create_mock_cell(self, text):
        """Helper method to create reusable mock cells."""
        mock_cell = Mock()
        mock_cell.inner_text = Mock(return_value=text)
        return mock_cell
    
    def _setup_mock_cells(self, mock_cells, cell_data):
        """Helper method to set up mock cells with reusable mocks."""
        mock_cells.nth = Mock(side_effect=lambda i: self._create_mock_cell(cell_data[i]))

    def test_complete_search_workflow_with_buat_environment(self):
        """Test complete search flow from number lookup to enhanced result with BUAT environment.
        
        This test covers the full workflow:
        1. Number lookup with Playwright page interactions
        2. Column extraction from table structure
        3. Environment detection based on numeric values
        4. Enhanced result building with all required fields
        5. Backward compatibility with existing tuple format
        
        Requirements: 1.1, 1.2, 2.1, 3.5, 4.1
        """
        # Arrange - Set up realistic BMP table structure with BUAT environment
        test_number = "TXN_BUAT_001"
        
        # Mock the number element locator
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        
        # Mock the parent row locator
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        # Mock table cells with realistic BMP data including BUAT environment
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 8
        
        # Realistic BMP transaction data with BUAT environment (27 in position 2 - first numeric)
        cell_data = [
            "REF_BUAT_001",      # Position 1: Reference
            "27-Q1",             # Position 2: Environment indicator (BUAT) - first numeric value
            "SWIFT_MT103",       # Position 3: Message type
            "USD",               # Position 4: Currency (backward compatibility)
            "PROCESSING",        # Position 5: Status
            "1500000.00",        # Position 6: Amount (second numeric, but first determines environment)
            "2024-01-15",        # Position 7: Date (second-to-last)
            "ACTIVE"             # Position 8: Final status (last column)
        ]
        
        # Mock individual cell responses with reusable mocks
        def create_mock_cell(text):
            mock_cell = Mock()
            mock_cell.inner_text = Mock(return_value=text)
            return mock_cell
        
        mock_cells.nth = Mock(side_effect=lambda i: create_mock_cell(cell_data[i]))
        
        # Mock the page locator to return our number element
        self.mock_page.locator.return_value = mock_number_element
        
        # Mock scrollIntoView evaluation
        mock_number_element.first.evaluate = Mock()
        
        # Act - Execute the complete enhanced search workflow
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert - Verify complete workflow results
        self.assertIsInstance(result, BPMSearchResult)
        
        # Verify backward compatibility fields (Requirements 1.1, 4.1)
        self.assertEqual(result.fourth_column, "USD")
        self.assertEqual(result.last_column, "ACTIVE")
        
        # Verify enhanced fields (Requirements 1.2, 2.1, 3.5, 4.1)
        self.assertEqual(result.second_to_last_column, "2024-01-15")
        self.assertEqual(result.environment, "buat")
        self.assertEqual(result.total_columns, 8)
        self.assertTrue(result.transaction_found)
        
        # Verify all columns are captured (Requirements 1.1, 1.2)
        self.assertEqual(len(result.all_columns), 8)
        self.assertEqual(result.all_columns[0].value, "REF_BUAT_001")
        self.assertEqual(result.all_columns[0].position, 1)
        self.assertEqual(result.all_columns[2].value, "27-Q1")
        self.assertTrue(result.all_columns[2].is_numeric)
        self.assertEqual(result.all_columns[2].numeric_value, 27)
        
        # Verify environment detection worked correctly (Requirements 3.5)
        # Should detect BUAT from first numeric value (27 in position 2)
        numeric_columns = [col for col in result.all_columns if col.is_numeric]
        first_numeric = next(col for col in result.all_columns if col.is_numeric)
        self.assertEqual(first_numeric.numeric_value, 27)
        self.assertEqual(first_numeric.position, 2)
        
        # Verify Playwright interactions occurred
        self.mock_page.locator.assert_called_with(f"div.tcell[title='{test_number}']")
        mock_number_element.count.assert_called_once()
        mock_number_element.first.evaluate.assert_called_once()
        self.bmp_page.wait_for_page_to_load.assert_called_once()

    def test_complete_search_workflow_with_uat_environment(self):
        """Test complete search flow with UAT environment detection.
        
        Requirements: 1.1, 1.2, 2.1, 3.5, 4.1
        """
        # Arrange - Set up table structure with UAT environment
        test_number = "TXN_UAT_002"
        
        # Mock Playwright elements
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        # Mock table cells with UAT environment (15 outside BUAT range)
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 6
        
        cell_data = [
            "REF_UAT_002",       # Position 1: Reference
            "15-PROD",           # Position 2: Environment indicator (UAT)
            "SWIFT_MT202",       # Position 3: Message type
            "EUR",               # Position 4: Currency
            "750.50",            # Position 5: Amount (second-to-last)
            "COMPLETED"          # Position 6: Status (last)
        ]
        
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "EUR")
        self.assertEqual(result.last_column, "COMPLETED")
        self.assertEqual(result.second_to_last_column, "750.50")
        self.assertEqual(result.environment, "uat")
        self.assertEqual(result.total_columns, 6)
        
        # Verify UAT detection from first numeric value 15
        first_numeric = next(col for col in result.all_columns if col.is_numeric)
        self.assertEqual(first_numeric.numeric_value, 15)
        self.assertEqual(first_numeric.value, "15-PROD")
        self.assertEqual(first_numeric.position, 2)

    def test_complete_search_workflow_with_unknown_environment(self):
        """Test complete search flow with unknown environment (no numeric values).
        
        Requirements: 1.1, 1.2, 2.1, 3.5, 4.1
        """
        # Arrange - Set up table structure with no numeric values
        test_number = "TXN_UNKNOWN_003"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        # All text values, no numeric content
        cell_data = [
            "REF_TEXT_ONLY",     # Position 1: Reference
            "PROCESSING",        # Position 2: Status
            "SWIFT_ALPHA",       # Position 3: Message type
            "GBP",               # Position 4: Currency (fourth column)
            "PENDING"            # Position 5: Status (last column)
        ]
        
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "GBP")
        self.assertEqual(result.last_column, "PENDING")
        self.assertEqual(result.second_to_last_column, "GBP")  # Same as 4th when only 5 columns
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 5)
        
        # Verify no numeric columns detected
        numeric_columns = [col for col in result.all_columns if col.is_numeric]
        self.assertEqual(len(numeric_columns), 0)

    def test_backward_compatibility_tuple_return(self):
        """Test that backward compatibility is maintained with tuple return format.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_COMPAT_004"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 6
        
        cell_data = ["COL1", "COL2", "COL3", "FOURTH", "COL5", "LAST"]  # No numeric values = unknown environment
        self._setup_mock_cells(mock_cells, cell_data)
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act - Test both enhanced and backward compatible returns
        enhanced_result = self.bmp_page.search_results(test_number, return_enhanced=True)
        tuple_result = self.bmp_page.search_results(test_number, return_enhanced=False)
        
        # Assert - Verify backward compatibility
        self.assertIsInstance(enhanced_result, BPMSearchResult)
        self.assertIsInstance(tuple_result, tuple)
        self.assertEqual(len(tuple_result), 2)
        
        # Verify same data in both formats
        self.assertEqual(tuple_result[0], enhanced_result.fourth_column)
        self.assertEqual(tuple_result[1], enhanced_result.last_column)
        self.assertEqual(tuple_result, ("FOURTH", "LAST"))

    def test_error_handling_no_element_found(self):
        """Test error handling when target number element is not found.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_NOT_FOUND"
        
        # Mock element not found scenario
        mock_number_element = Mock()
        mock_number_element.count.return_value = 0
        self.mock_page.locator.return_value = mock_number_element
        
        # Act - Should return not found result instead of raising exception
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert - Should return not found result
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertFalse(result.transaction_found)

    def test_error_handling_multiple_elements_found(self):
        """Test error handling when multiple elements are found.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_MULTIPLE"
        
        # Mock multiple elements found
        mock_number_element = Mock()
        mock_number_element.count.return_value = 3
        mock_number_element.first = Mock()
        
        # Mock successful first element processing
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 4
        
        cell_data = ["MULTI1", "MULTI2", "MULTI3", "MULTI4"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert - Should handle multiple elements by using first one
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "MULTI4")
        self.assertEqual(result.last_column, "MULTI4")
        self.assertTrue(result.transaction_found)

    def test_error_handling_column_extraction_failure(self):
        """Test error handling when column extraction fails.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_EXTRACT_FAIL"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        # Mock column extraction failure
        mock_parent_row.locator.side_effect = Exception("Column extraction failed")
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert - Should fall back gracefully
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertFalse(result.transaction_found)

    def test_error_handling_individual_cell_failures(self):
        """Test error handling when individual cells fail to extract.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_CELL_FAIL"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        # Mock some cells succeeding and others failing
        mock_cell1 = Mock()
        mock_cell1.inner_text.return_value = "26-BUAT"  # First cell with BUAT value (first numeric)
        
        mock_cell2 = Mock()
        mock_cell2.inner_text.side_effect = Exception("Cell 2 failed")
        
        mock_cell3 = Mock()
        mock_cell3.inner_text.return_value = "GOOD_CELL_3"
        
        mock_cell4 = Mock()
        mock_cell4.inner_text.return_value = "GOOD_CELL_4"
        
        mock_cell5 = Mock()
        mock_cell5.inner_text.side_effect = Exception("Cell 5 failed")
        
        mock_cells.nth.side_effect = [mock_cell1, mock_cell2, mock_cell3, mock_cell4, mock_cell5]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert - Should handle partial failures gracefully
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.total_columns, 5)
        self.assertEqual(result.environment, "buat")  # Should still detect from good cell
        
        # Verify good cells are preserved
        self.assertEqual(result.all_columns[0].value, "26-BUAT")
        self.assertEqual(result.all_columns[2].value, "GOOD_CELL_3")
        self.assertEqual(result.all_columns[3].value, "GOOD_CELL_4")
        
        # Verify failed cells have empty values (safe extraction)
        self.assertEqual(result.all_columns[1].value, "")
        self.assertEqual(result.all_columns[4].value, "")

    def test_edge_case_minimal_table_structure(self):
        """Test edge case with minimal table structure (2 columns).
        
        Requirements: 1.1, 1.2, 2.1, 4.1
        """
        # Arrange
        test_number = "TXN_MINIMAL"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 2
        
        cell_data = ["FIRST", "LAST"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "NotFound")  # No 4th column
        self.assertEqual(result.last_column, "LAST")
        self.assertEqual(result.second_to_last_column, "FIRST")  # First becomes second-to-last
        self.assertEqual(result.total_columns, 2)
        self.assertEqual(len(result.all_columns), 2)

    def test_edge_case_single_column_table(self):
        """Test edge case with single column table.
        
        Requirements: 1.1, 1.2, 2.1, 4.1
        """
        # Arrange
        test_number = "TXN_SINGLE"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 1
        
        cell_data = ["ONLY_COLUMN"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "ONLY_COLUMN")
        self.assertEqual(result.second_to_last_column, "NotFound")  # No second-to-last
        self.assertEqual(result.total_columns, 1)

    def test_edge_case_large_table_structure(self):
        """Test edge case with large table structure (15 columns).
        
        Requirements: 1.1, 1.2, 2.1, 4.1
        """
        # Arrange
        test_number = "TXN_LARGE"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 15
        
        # Generate 15 columns of data with BUAT environment in position 2 (first numeric)
        cell_data = [f"COL_{i+1}" for i in range(15)]
        cell_data[1] = "28-BUAT"  # Position 2 (0-indexed 1) has BUAT value as first numeric
        
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        self.assertIsInstance(result, BPMSearchResult)
        self.assertEqual(result.fourth_column, "COL_4")
        self.assertEqual(result.last_column, "COL_15")
        self.assertEqual(result.second_to_last_column, "COL_14")
        self.assertEqual(result.environment, "buat")
        self.assertEqual(result.total_columns, 15)
        self.assertEqual(len(result.all_columns), 15)
        
        # Verify environment detection from position 2 (first numeric)
        buat_column = result.all_columns[1]  # 0-indexed position 2
        self.assertEqual(buat_column.value, "28-BUAT")
        self.assertTrue(buat_column.is_numeric)
        self.assertEqual(buat_column.numeric_value, 28)

    def test_realistic_bmp_transaction_scenarios(self):
        """Test realistic BMP transaction scenarios with various data patterns.
        
        Requirements: 1.1, 1.2, 2.1, 3.5, 4.1
        """
        # Test multiple realistic scenarios
        scenarios = [
            {
                "name": "SWIFT_MT103_BUAT",
                "number": "REF20240115001",
                "data": [
                    "REF20240115001",
                    "25-Q1",              # First numeric value (BUAT range)
                    "SWIFT_MT103",
                    "USD",
                    "PROCESSING",
                    "5000000.00",         # Second numeric value (ignored for environment)
                    "2024-01-15T14:30:00Z", # Third numeric value (ignored for environment)
                    "ACTIVE"
                ],
                "expected_env": "buat",
                "expected_numeric": 25
            },
            {
                "name": "SEPA_INSTANT_UAT",
                "number": "SEPA20240115002",
                "data": [
                    "SEPA20240115002",
                    "10-PROD",            # First numeric value (UAT - outside 25-29)
                    "SEPA_INSTANT",
                    "EUR",
                    "COMPLETED",
                    "999.99",             # Second numeric value (ignored for environment)
                    "SETTLED"
                ],
                "expected_env": "uat",
                "expected_numeric": 10
            },
            {
                "name": "FEDWIRE_UNKNOWN",
                "number": "FED20240115003",
                "data": [
                    "FED20240115003",
                    "FEDWIRE",
                    "USD",
                    "PENDING",
                    "VALIDATION",
                    "QUEUED"
                ],
                "expected_env": "unknown",
                "expected_numeric": None
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                # Arrange
                mock_number_element = Mock()
                mock_number_element.count.return_value = 1
                mock_number_element.first = Mock()
                mock_parent_row = Mock()
                mock_number_element.first.locator.return_value = mock_parent_row
                
                mock_cells = Mock()
                mock_parent_row.locator.return_value = mock_cells
                mock_cells.count.return_value = len(scenario["data"])
                
                mock_cells.nth.side_effect = [
                    Mock(inner_text=Mock(return_value=text)) for text in scenario["data"]
                ]
                
                self.mock_page.locator.return_value = mock_number_element
                mock_number_element.first.evaluate = Mock()
                
                # Act
                result = self.bmp_page.search_results(scenario["number"], return_enhanced=True)
                
                # Assert
                self.assertIsInstance(result, BPMSearchResult)
                self.assertEqual(result.environment, scenario["expected_env"])
                self.assertEqual(result.total_columns, len(scenario["data"]))
                self.assertTrue(result.transaction_found)
                
                # Verify specific numeric detection if expected
                if scenario["expected_numeric"] is not None:
                    numeric_columns = [col for col in result.all_columns if col.is_numeric]
                    self.assertTrue(any(col.numeric_value == scenario["expected_numeric"] for col in numeric_columns))

    def test_logging_integration(self):
        """Test that enhanced logging is properly integrated throughout the workflow.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_LOGGING"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 6
        
        cell_data = ["REF001", "29-Q4", "SWIFT", "GBP", "1000.00", "DONE"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act with logging capture
        with patch('logging.info') as mock_log_info:
            result = self.bmp_page.search_results(test_number, return_enhanced=True)
            
            # Assert logging occurred
            self.assertTrue(mock_log_info.called)
            
            # Verify specific log messages for enhanced fields
            log_calls = [call.args[0] for call in mock_log_info.call_args_list]
            
            # Should log traditional values for backward compatibility
            self.assertTrue(any("4th Column Value:" in msg for msg in log_calls))
            self.assertTrue(any("Last Column Value:" in msg for msg in log_calls))
            
            # Should log enhanced values
            self.assertTrue(any("Second-to-Last Column Value:" in msg for msg in log_calls))
            self.assertTrue(any("Environment Detected:" in msg for msg in log_calls))
            self.assertTrue(any("Total Columns:" in msg for msg in log_calls))

    def test_serialization_integration(self):
        """Test that enhanced results can be properly serialized for JSON output.
        
        Requirements: 4.1
        """
        # Arrange
        test_number = "TXN_SERIALIZE"
        
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_number_element.first = Mock()
        mock_parent_row = Mock()
        mock_number_element.first.locator.return_value = mock_parent_row
        
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        cell_data = ["SER001", "26", "TEST", "USD", "FINAL"]  # 26 is first numeric (BUAT)
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_data
        ]
        
        self.mock_page.locator.return_value = mock_number_element
        mock_number_element.first.evaluate = Mock()
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        serialized = result.to_dict()
        
        # Assert
        self.assertIsInstance(serialized, dict)
        
        # Verify all required fields are present and serializable
        required_fields = [
            "fourth_column", "last_column", "second_to_last_column",
            "environment", "total_columns", "transaction_found",
            "search_timestamp", "all_columns"
        ]
        
        for field in required_fields:
            self.assertIn(field, serialized)
        
        # Verify column data serialization
        self.assertEqual(len(serialized["all_columns"]), 5)
        self.assertEqual(serialized["all_columns"][1]["value"], "26")
        self.assertTrue(serialized["all_columns"][1]["is_numeric"])
        self.assertEqual(serialized["all_columns"][1]["numeric_value"], 26)
        
        # Verify environment and metadata
        self.assertEqual(serialized["environment"], "buat")
        self.assertEqual(serialized["total_columns"], 5)
        self.assertTrue(serialized["transaction_found"])

    def tearDown(self):
        """Clean up test fixtures."""
        # Reset any global state if needed
        pass


if __name__ == '__main__':
    # Configure logging for test execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the tests
    unittest.main(verbosity=2)