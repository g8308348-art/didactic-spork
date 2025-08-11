"""Unit tests for comprehensive column extraction functionality.

Tests the _extract_all_columns method with different table structures,
varying column counts, and error scenarios.
"""

import unittest
from unittest.mock import Mock, MagicMock
import logging
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bpm.bpm_page import BPMPage, ColumnData


class TestColumnExtraction(unittest.TestCase):
    """Test cases for the _extract_all_columns method."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the Playwright page object
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)
        
        # Set up logging to capture debug messages
        logging.basicConfig(level=logging.DEBUG)

    def test_extract_all_columns_standard_case(self):
        """Test column extraction with standard 6-column table structure."""
        # Mock parent row with 6 columns
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 6
        
        # Mock cell data - mix of text and numeric values
        cell_texts = ["TXN123", "PENDING", "25-Q1", "APPROVED", "100.50", "2024-01-15"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 6)
        
        # Check first column (text with number)
        self.assertEqual(result[0].position, 1)
        self.assertEqual(result[0].value, "TXN123")
        self.assertTrue(result[0].is_numeric)  # Should extract "123"
        self.assertEqual(result[0].numeric_value, 123)
        
        # Check third column (numeric with text)
        self.assertEqual(result[2].position, 3)
        self.assertEqual(result[2].value, "25-Q1")
        self.assertTrue(result[2].is_numeric)
        self.assertEqual(result[2].numeric_value, 25)
        
        # Check fifth column (decimal number)
        self.assertEqual(result[4].position, 5)
        self.assertEqual(result[4].value, "100.50")
        self.assertTrue(result[4].is_numeric)
        self.assertEqual(result[4].numeric_value, 100)

    def test_extract_all_columns_minimal_case(self):
        """Test column extraction with minimal 2-column table."""
        # Mock parent row with only 2 columns
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 2
        
        # Mock cell data
        cell_texts = ["ID001", "COMPLETE"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].position, 1)
        self.assertEqual(result[0].value, "ID001")
        self.assertEqual(result[1].position, 2)
        self.assertEqual(result[1].value, "COMPLETE")

    def test_extract_all_columns_extended_case(self):
        """Test column extraction with extended 10+ column table."""
        # Mock parent row with 12 columns
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 12
        
        # Mock cell data with various formats
        cell_texts = [
            "TXN456", "PROCESSING", "27-UAT", "SWIFT", "EUR", "1000.00",
            "2024-01-15", "BANK_A", "BANK_B", "REF123", "URGENT", "SUCCESS"
        ]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 12)
        
        # Check that positions are correctly assigned
        for i, column in enumerate(result):
            self.assertEqual(column.position, i + 1)
            self.assertEqual(column.value, cell_texts[i])
        
        # Check specific numeric detection
        self.assertTrue(result[2].is_numeric)  # "27-UAT"
        self.assertEqual(result[2].numeric_value, 27)
        self.assertTrue(result[5].is_numeric)  # "1000.00"
        self.assertEqual(result[5].numeric_value, 1000)

    def test_extract_all_columns_empty_columns(self):
        """Test column extraction with some empty columns."""
        # Mock parent row with columns containing empty values
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 5
        
        # Mock cell data with empty values
        cell_texts = ["TXN789", "", "25", "", "FINAL"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 5)
        
        # Check empty columns
        self.assertEqual(result[1].value, "")
        self.assertFalse(result[1].is_numeric)
        self.assertEqual(result[3].value, "")
        self.assertFalse(result[3].is_numeric)
        
        # Check numeric column
        self.assertEqual(result[2].value, "25")
        self.assertTrue(result[2].is_numeric)
        self.assertEqual(result[2].numeric_value, 25)

    def test_extract_all_columns_special_characters(self):
        """Test column extraction with special characters and Unicode."""
        # Mock parent row with special characters
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 4
        
        # Mock cell data with special characters
        cell_texts = ["TXN@123", "STATUS_PENDING", "€1,234.56", "Müller & Co."]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 4)
        
        # Check special character handling
        self.assertEqual(result[0].value, "TXN@123")
        self.assertTrue(result[0].is_numeric)  # Should extract "123"
        self.assertEqual(result[0].numeric_value, 123)
        
        self.assertEqual(result[2].value, "€1,234.56")
        self.assertTrue(result[2].is_numeric)  # Should extract "1"
        self.assertEqual(result[2].numeric_value, 1)
        
        self.assertEqual(result[3].value, "Müller & Co.")
        self.assertFalse(result[3].is_numeric)

    def test_extract_all_columns_no_cells_found(self):
        """Test column extraction when no cells are found in the row."""
        # Mock parent row with no cells
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 0
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 0)

    def test_extract_all_columns_none_parent_row(self):
        """Test column extraction with None parent row."""
        # Execute the method with None
        result = self.bmp_page._extract_all_columns(None)
        
        # Verify results
        self.assertEqual(len(result), 0)

    def test_extract_all_columns_cell_text_extraction_error(self):
        """Test column extraction when individual cell text extraction fails."""
        # Mock parent row
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 3
        
        # Mock cells where second cell throws an exception
        mock_cell1 = Mock()
        mock_cell1.inner_text.return_value = "GOOD_CELL"
        
        mock_cell2 = Mock()
        mock_cell2.inner_text.side_effect = Exception("Text extraction failed")
        
        mock_cell3 = Mock()
        mock_cell3.inner_text.return_value = "ANOTHER_GOOD_CELL"
        
        mock_cells.nth.side_effect = [mock_cell1, mock_cell2, mock_cell3]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 3)
        
        # Check that good cells are processed correctly
        self.assertEqual(result[0].value, "GOOD_CELL")
        self.assertEqual(result[2].value, "ANOTHER_GOOD_CELL")
        
        # Check that failed cell gets empty string
        self.assertEqual(result[1].value, "")
        self.assertFalse(result[1].is_numeric)

    def test_extract_all_columns_cell_access_error(self):
        """Test column extraction when accessing a cell fails completely."""
        # Mock parent row
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 3
        
        # Mock cells where second cell access throws an exception
        mock_cell1 = Mock()
        mock_cell1.inner_text.return_value = "CELL_1"
        
        mock_cell3 = Mock()
        mock_cell3.inner_text.return_value = "CELL_3"
        
        def mock_nth(index):
            if index == 0:
                return mock_cell1
            elif index == 1:
                raise Exception("Cell access failed")
            elif index == 2:
                return mock_cell3
        
        mock_cells.nth.side_effect = mock_nth
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 3)
        
        # Check that good cells are processed correctly
        self.assertEqual(result[0].value, "CELL_1")
        self.assertEqual(result[2].value, "CELL_3")
        
        # Check that failed cell gets placeholder
        self.assertEqual(result[1].value, "ExtractionError")
        self.assertFalse(result[1].is_numeric)
        self.assertEqual(result[1].position, 2)

    def test_extract_all_columns_critical_error(self):
        """Test column extraction when a critical error occurs."""
        # Mock parent row that throws exception on locator call
        mock_parent_row = Mock()
        mock_parent_row.locator.side_effect = Exception("Critical locator error")
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results - should return empty list
        self.assertEqual(len(result), 0)

    def test_extract_all_columns_whitespace_handling(self):
        """Test column extraction with whitespace in cell values."""
        # Mock parent row with whitespace in cells
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 4
        
        # Mock cell data with various whitespace scenarios
        cell_texts = ["  TXN123  ", "\tSTATUS\t", "\n25-Q1\n", "   "]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results - whitespace should be stripped
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].value, "TXN123")
        self.assertEqual(result[1].value, "STATUS")
        self.assertEqual(result[2].value, "25-Q1")
        self.assertEqual(result[3].value, "")  # Only whitespace becomes empty string

    def test_extract_all_columns_numeric_edge_cases(self):
        """Test column extraction with various numeric edge cases."""
        # Mock parent row with numeric edge cases
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_parent_row.locator.return_value = mock_cells
        mock_cells.count.return_value = 6
        
        # Mock cell data with numeric edge cases
        cell_texts = ["-25", "0", "999999", "25.0", "ENV-29", "NO_NUMBERS"]
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value=text)) for text in cell_texts
        ]
        
        # Execute the method
        result = self.bmp_page._extract_all_columns(mock_parent_row)
        
        # Verify results
        self.assertEqual(len(result), 6)
        
        # Check negative number
        self.assertTrue(result[0].is_numeric)
        self.assertEqual(result[0].numeric_value, -25)
        
        # Check zero
        self.assertTrue(result[1].is_numeric)
        self.assertEqual(result[1].numeric_value, 0)
        
        # Check large number
        self.assertTrue(result[2].is_numeric)
        self.assertEqual(result[2].numeric_value, 999999)
        
        # Check decimal
        self.assertTrue(result[3].is_numeric)
        self.assertEqual(result[3].numeric_value, 25)
        
        # Check mixed text with number
        self.assertTrue(result[4].is_numeric)
        self.assertEqual(result[4].numeric_value, 29)
        
        # Check no numbers
        self.assertFalse(result[5].is_numeric)
        self.assertIsNone(result[5].numeric_value)


if __name__ == '__main__':
    unittest.main()