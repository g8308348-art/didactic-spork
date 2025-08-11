"""Integration tests for column extraction with existing BPM functionality.

Tests the integration of _extract_all_columns with the existing look_for_number
method and environment detection functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock
import logging
import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from bpm.bpm_page import BPMPage, ColumnData


class TestColumnExtractionIntegration(unittest.TestCase):
    """Integration test cases for column extraction with existing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the Playwright page object
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)
        
        # Set up logging to capture debug messages
        logging.basicConfig(level=logging.DEBUG)

    def test_extract_columns_with_environment_detection_buat(self):
        """Test column extraction integrated with environment detection for BUAT."""
        # Mock parent row with columns containing BUAT range values
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 6
        
        # Mock cell data with BUAT environment (value 27)
        # Note: TXN456 will extract 456 (UAT), but 27-UAT should be processed first due to position
        cell_texts = ["TXN_NO_NUM", "PROCESSING", "27-UAT", "APPROVED", "500.00", "2024-01-15"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute column extraction
        columns = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Execute environment detection
        environment = self.bmp_page._detect_environment(columns)
        
        # Verify results
        self.assertEqual(len(columns), 6)
        self.assertEqual(environment, "buat")
        
        # Verify the column that triggered BUAT detection
        self.assertEqual(columns[2].value, "27-UAT")
        self.assertTrue(columns[2].is_numeric)
        self.assertEqual(columns[2].numeric_value, 27)

    def test_extract_columns_with_environment_detection_uat(self):
        """Test column extraction integrated with environment detection for UAT."""
        # Mock parent row with columns containing UAT range values
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        # Mock cell data with UAT environment (value 15)
        cell_texts = ["TXN789", "COMPLETE", "15-PROD", "SUCCESS", "750.25"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute column extraction
        columns = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Execute environment detection
        environment = self.bmp_page._detect_environment(columns)
        
        # Verify results
        self.assertEqual(len(columns), 5)
        self.assertEqual(environment, "uat")
        
        # Verify the column that triggered UAT detection
        self.assertEqual(columns[2].value, "15-PROD")
        self.assertTrue(columns[2].is_numeric)
        self.assertEqual(columns[2].numeric_value, 15)

    def test_extract_columns_with_environment_detection_unknown(self):
        """Test column extraction integrated with environment detection for unknown."""
        # Mock parent row with columns containing no numeric values
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 4
        
        # Mock cell data with no numeric values
        cell_texts = ["TXN_ABC", "PENDING", "STATUS_OK", "FINAL"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute column extraction
        columns = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Execute environment detection
        environment = self.bmp_page._detect_environment(columns)
        
        # Verify results
        self.assertEqual(len(columns), 4)
        self.assertEqual(environment, "unknown")
        
        # Verify no columns are numeric
        for column in columns:
            self.assertFalse(column.is_numeric)

    def test_extract_columns_backward_compatibility_data(self):
        """Test that column extraction provides data for backward compatibility."""
        # Mock parent row with standard table structure
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 8
        
        # Mock cell data - ensure 4th and last columns have specific values
        cell_texts = ["COL1", "COL2", "COL3", "FOURTH_COL", "COL5", "COL6", "SECOND_LAST", "LAST_COL"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute column extraction
        columns = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(columns), 8)
        
        # Verify backward compatibility data is available
        fourth_column = columns[3].value if len(columns) > 3 else "NotFound"
        last_column = columns[-1].value if len(columns) > 0 else "NotFound"
        second_to_last = columns[-2].value if len(columns) > 1 else "NotFound"
        
        self.assertEqual(fourth_column, "FOURTH_COL")
        self.assertEqual(last_column, "LAST_COL")
        self.assertEqual(second_to_last, "SECOND_LAST")

    def test_extract_columns_varying_column_counts(self):
        """Test column extraction with different table structures."""
        test_cases = [
            # (column_count, expected_positions)
            (2, [1, 2]),
            (4, [1, 2, 3, 4]),
            (10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ]
        
        for column_count, expected_positions in test_cases:
            with self.subTest(column_count=column_count):
                # Mock parent row
                mock_parent_row = Mock()
                mock_cells = Mock()
                mock_parent_row.locator.return_value = mock_cells
                mock_cells.count.return_value = column_count
                
                # Mock cell data
                cell_texts = [f"COL_{i+1}" for i in range(column_count)]
                mock_cells.nth.side_effect = [
                    Mock(inner_text=Mock(return_value=text)) for text in cell_texts
                ]
                
                # Execute column extraction
                columns = self.bmp_page._extract_all_columns(mock_parent_row)
                
                # Verify results
                self.assertEqual(len(columns), column_count)
                
                # Verify positions are correct
                actual_positions = [col.position for col in columns]
                self.assertEqual(actual_positions, expected_positions)
                
                # Verify values are correct
                actual_values = [col.value for col in columns]
                self.assertEqual(actual_values, cell_texts)

    def test_extract_columns_with_mixed_data_types(self):
        """Test column extraction with realistic mixed data types."""
        # Mock parent row with realistic BPM data
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 7
        
        # Mock realistic BPM cell data
        cell_texts = [
            "TXN_ALPHA",       # Transaction ID (no numbers)
            "SWIFT_MT_ALPHA",  # Message type (no numbers)
            "25-Q1",           # Environment indicator (BUAT) - should be detected first
            "PROCESSING",      # Status
            "USD",             # Currency
            "1000000.00",      # Amount
            "2024-01-15T10:30:00Z"  # Timestamp
        ]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute column extraction
        columns = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Execute environment detection
        environment = self.bmp_page._detect_environment(columns)
        
        # Verify results
        self.assertEqual(len(columns), 7)
        self.assertEqual(environment, "buat")
        
        # Verify specific column parsing
        # Transaction ID should have no numeric part
        self.assertFalse(columns[0].is_numeric)
        self.assertIsNone(columns[0].numeric_value)
        
        # Environment indicator should extract 25
        self.assertTrue(columns[2].is_numeric)
        self.assertEqual(columns[2].numeric_value, 25)
        
        # Amount should extract integer part
        self.assertTrue(columns[5].is_numeric)
        self.assertEqual(columns[5].numeric_value, 1000000)
        
        # Timestamp should extract first number (2024)
        self.assertTrue(columns[6].is_numeric)
        self.assertEqual(columns[6].numeric_value, 2024)

    def test_extract_columns_error_recovery(self):
        """Test that column extraction recovers gracefully from errors."""
        # Mock parent row where some cells fail
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        # Mock cells with some failures
        mock_cell1 = Mock()
        mock_cell1.inner_text.return_value = "GOOD_CELL_NO_NUM"  # No numbers
        
        mock_cell2 = Mock()
        mock_cell2.inner_text.side_effect = Exception("Cell 2 failed")
        
        mock_cell3 = Mock()
        mock_cell3.inner_text.return_value = "GOOD_CELL_ALSO_NO_NUM"  # No numbers
        
        mock_cell4 = Mock()
        mock_cell4.inner_text.return_value = "26-BUAT"  # Should trigger BUAT
        
        mock_cell5 = Mock()
        mock_cell5.inner_text.side_effect = Exception("Cell 5 failed")
        
        mock_cells.nth.side_effect = [mock_cell1, mock_cell2, mock_cell3, mock_cell4, mock_cell5]
        
        # Execute column extraction
        columns = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Execute environment detection
        environment = self.bmp_page._detect_environment(columns)
        
        # Verify results
        self.assertEqual(len(columns), 5)
        self.assertEqual(environment, "buat")  # Should still detect from good cell
        
        # Verify good cells are processed correctly
        self.assertEqual(columns[0].value, "GOOD_CELL_NO_NUM")
        self.assertEqual(columns[2].value, "GOOD_CELL_ALSO_NO_NUM")
        self.assertEqual(columns[3].value, "26-BUAT")
        
        # Verify failed cells have error placeholders
        self.assertEqual(columns[1].value, "")  # Text extraction failed
        self.assertEqual(columns[4].value, "")  # Text extraction failed


if __name__ == '__main__':
    unittest.main()