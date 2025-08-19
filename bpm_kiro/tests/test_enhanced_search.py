"""Unit tests for enhanced look_for_number method functionality.

This module tests the enhanced search functionality including:
- Integration of column extraction logic
- Environment detection in search flow
- Backward compatibility with tuple return format
- Comprehensive error handling with fallback behavior
- Enhanced logging for new data fields
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import logging
from datetime import datetime

# Import the classes we need to test
from bpm.bpm_page import BPMPage, ColumnData, BPMSearchResult


class TestEnhancedSearch(unittest.TestCase):
    """Test cases for enhanced look_for_number method functionality."""

    def setUp(self):
        """Set up test fixtures with mocked Playwright page."""
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)
        
        # Set up logging to capture log messages during tests
        self.log_messages = []
        self.log_handler = logging.Handler()
        self.log_handler.emit = lambda record: self.log_messages.append(record.getMessage())
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.DEBUG)

    def tearDown(self):
        """Clean up test fixtures."""
        logging.getLogger().removeHandler(self.log_handler)
        self.log_messages.clear()

    def test_enhanced_search_successful_extraction(self):
        """Test successful enhanced search with column extraction and environment detection."""
        # Arrange
        test_number = "12345"
        
        # Mock the page locator chain for finding the number
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        # Mock the parent row locator
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock column data for enhanced extraction
        test_columns = [
            ColumnData(position=1, value="COL1", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="COL2", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="COL3", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="FOURTH_COL", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="25-Q1", is_numeric=True, numeric_value=25),
            ColumnData(position=6, value="LAST_COL", is_numeric=False, numeric_value=None)
        ]
        
        # Mock the helper methods
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=test_columns):
            with patch.object(self.bmp_page, '_detect_environment', return_value="buat"):
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert
                self.assertEqual(result, ("FOURTH_COL", "LAST_COL"))
                
                # Verify enhanced logging occurred
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Enhanced search completed", log_messages_str)
                self.assertIn("Total columns: 6", log_messages_str)
                self.assertIn("Environment detected: buat", log_messages_str)
                self.assertIn("Second-to-last column: 25-Q1", log_messages_str)

    def test_enhanced_search_with_uat_environment(self):
        """Test enhanced search detecting UAT environment."""
        # Arrange
        test_number = "67890"
        
        # Mock the page locator chain
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock column data with UAT environment (numeric value outside 25-29)
        test_columns = [
            ColumnData(position=1, value="COL1", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="30-Q2", is_numeric=True, numeric_value=30),  # UAT value
            ColumnData(position=3, value="COL3", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="FOURTH_VAL", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="LAST_VAL", is_numeric=False, numeric_value=None)
        ]
        
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=test_columns):
            with patch.object(self.bmp_page, '_detect_environment', return_value="uat"):
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert
                self.assertEqual(result, ("FOURTH_VAL", "LAST_VAL"))
                
                # Verify UAT environment was logged
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Environment detected: uat", log_messages_str)

    def test_enhanced_search_unknown_environment(self):
        """Test enhanced search with unknown environment (no numeric values)."""
        # Arrange
        test_number = "11111"
        
        # Mock the page locator chain
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock column data with no numeric values
        test_columns = [
            ColumnData(position=1, value="TEXT1", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="TEXT2", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="TEXT3", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="FOURTH_TEXT", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="LAST_TEXT", is_numeric=False, numeric_value=None)
        ]
        
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=test_columns):
            with patch.object(self.bmp_page, '_detect_environment', return_value="unknown"):
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert
                self.assertEqual(result, ("FOURTH_TEXT", "LAST_TEXT"))
                
                # Verify unknown environment was logged
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Environment detected: unknown", log_messages_str)

    def test_enhanced_search_fallback_to_original_on_empty_columns(self):
        """Test fallback to original extraction when enhanced extraction returns no columns."""
        # Arrange
        test_number = "22222"
        
        # Mock the page locator chain
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock enhanced extraction returning empty columns
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=[]):
            with patch.object(self.bmp_page, '_fallback_to_original_extraction', return_value=("FALLBACK_FOURTH", "FALLBACK_LAST")) as mock_fallback:
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert
                self.assertEqual(result, ("FALLBACK_FOURTH", "FALLBACK_LAST"))
                mock_fallback.assert_called_once_with(mock_parent_row)
                
                # Verify fallback warning was logged
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Enhanced extraction returned no columns", log_messages_str)
                self.assertIn("falling back to original method", log_messages_str)

    def test_enhanced_search_fallback_on_extraction_exception(self):
        """Test fallback to original extraction when enhanced extraction raises exception."""
        # Arrange
        test_number = "33333"
        
        # Mock the page locator chain
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock enhanced extraction raising an exception
        with patch.object(self.bmp_page, '_extract_all_columns', side_effect=Exception("Extraction failed")):
            with patch.object(self.bmp_page, '_fallback_to_original_extraction', return_value=("FALLBACK_FOURTH", "FALLBACK_LAST")) as mock_fallback:
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert
                self.assertEqual(result, ("FALLBACK_FOURTH", "FALLBACK_LAST"))
                mock_fallback.assert_called_once_with(mock_parent_row)
                
                # Verify fallback warning was logged
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Enhanced extraction failed", log_messages_str)
                self.assertIn("Falling back to original column extraction method", log_messages_str)

    def test_enhanced_search_number_not_found(self):
        """Test enhanced search when number is not found on page."""
        # Arrange
        test_number = "99999"
        
        # Mock the page locator returning no elements
        mock_number_element = Mock()
        mock_number_element.count.return_value = 0
        self.mock_page.locator.return_value = mock_number_element
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.bmp_page.look_for_number(test_number)
        
        self.assertIn("Number 99999 is not visible", str(context.exception))

    def test_enhanced_search_multiple_elements_found(self):
        """Test enhanced search when multiple elements are found."""
        # Arrange
        test_number = "44444"
        
        # Mock the page locator chain for multiple elements
        mock_number_element = Mock()
        mock_number_element.count.return_value = 2
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock successful enhanced extraction
        test_columns = [
            ColumnData(position=1, value="COL1", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="COL2", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="COL3", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="MULTI_FOURTH", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="MULTI_LAST", is_numeric=False, numeric_value=None)
        ]
        
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=test_columns):
            with patch.object(self.bmp_page, '_detect_environment', return_value="unknown"):
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert
                self.assertEqual(result, ("MULTI_FOURTH", "MULTI_LAST"))
                
                # Verify multiple elements message was logged
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Found 2 instances of number: 44444. Using the first match.", log_messages_str)

    def test_fallback_to_original_extraction_success(self):
        """Test successful fallback to original extraction method."""
        # Arrange
        mock_parent_row = Mock()
        
        # Mock the original locator calls
        mock_fourth_column = Mock()
        mock_fourth_column.inner_text.return_value = "ORIGINAL_FOURTH"
        mock_last_column = Mock()
        mock_last_column.inner_text.return_value = "ORIGINAL_LAST"
        
        mock_parent_row.locator.side_effect = [mock_fourth_column, mock_last_column]
        
        # Act
        result = self.bmp_page._fallback_to_original_extraction(mock_parent_row)
        
        # Assert
        self.assertEqual(result, ("ORIGINAL_FOURTH", "ORIGINAL_LAST"))
        
        # Verify correct locator calls were made
        expected_calls = [
            unittest.mock.call("div.tcell:nth-child(4)"),
            unittest.mock.call("div.tcell:last-child")
        ]
        mock_parent_row.locator.assert_has_calls(expected_calls)
        
        # Verify success message was logged
        log_messages_str = " ".join(self.log_messages)
        self.assertIn("Fallback extraction successful", log_messages_str)

    def test_fallback_to_original_extraction_failure(self):
        """Test fallback to original extraction when it also fails."""
        # Arrange
        mock_parent_row = Mock()
        
        # Mock the original locator calls to raise exception
        mock_parent_row.locator.side_effect = Exception("Locator failed")
        
        # Act
        result = self.bmp_page._fallback_to_original_extraction(mock_parent_row)
        
        # Assert
        self.assertEqual(result, ("NotFound", "NotFound"))
        
        # Verify error message was logged
        log_messages_str = " ".join(self.log_messages)
        self.assertIn("Fallback extraction also failed", log_messages_str)

    def test_enhanced_search_maintains_backward_compatibility(self):
        """Test that enhanced search maintains exact backward compatibility with tuple return."""
        # Arrange
        test_number = "55555"
        
        # Mock the page locator chain
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock column data
        test_columns = [
            ColumnData(position=1, value="A", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="B", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="C", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="BACKWARD_COMPAT_FOURTH", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="E", is_numeric=False, numeric_value=None),
            ColumnData(position=6, value="BACKWARD_COMPAT_LAST", is_numeric=False, numeric_value=None)
        ]
        
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=test_columns):
            with patch.object(self.bmp_page, '_detect_environment', return_value="unknown"):
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert - verify exact tuple format and values
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)
                self.assertEqual(result[0], "BACKWARD_COMPAT_FOURTH")
                self.assertEqual(result[1], "BACKWARD_COMPAT_LAST")

    def test_enhanced_search_with_minimal_columns(self):
        """Test enhanced search with minimal column count (less than 4 columns)."""
        # Arrange
        test_number = "66666"
        
        # Mock the page locator chain
        mock_number_element = Mock()
        mock_number_element.count.return_value = 1
        mock_first_element = Mock()
        mock_number_element.first = mock_first_element
        self.mock_page.locator.return_value = mock_number_element
        
        mock_parent_row = Mock()
        mock_first_element.locator.return_value = mock_parent_row
        
        # Mock column data with only 2 columns
        test_columns = [
            ColumnData(position=1, value="FIRST", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="SECOND", is_numeric=False, numeric_value=None)
        ]
        
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=test_columns):
            with patch.object(self.bmp_page, '_detect_environment', return_value="unknown"):
                # Act
                result = self.bmp_page.look_for_number(test_number)
                
                # Assert - should handle missing 4th column gracefully
                self.assertEqual(result, ("NotFound", "SECOND"))  # 4th column NotFound, last column is SECOND
                
                # Verify logging shows correct column count
                log_messages_str = " ".join(self.log_messages)
                self.assertIn("Total columns: 2", log_messages_str)


if __name__ == '__main__':
    # Configure logging for test execution
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    # Run the tests
    unittest.main()