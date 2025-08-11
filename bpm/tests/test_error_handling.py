"""
Unit tests for comprehensive error handling in BMP data enhancement.

This module tests the error handling scenarios and fallback behavior
for the enhanced column extraction functionality, ensuring graceful
degradation when column extraction fails.

Tests cover:
- _safe_extract_columns method with various error conditions
- _handle_extraction_failure method for fallback scenarios  
- Graceful degradation when column extraction fails
- Appropriate error logging without exposing sensitive data
- Fallback behavior for error scenarios

Requirements tested: 5.1, 5.2, 5.3, 5.5
"""

import logging
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from playwright.sync_api import Page

from bpm.bpm_page import BPMPage, ColumnData, BPMSearchResult


class TestSafeExtractColumns:
    """Test the _safe_extract_columns method with comprehensive error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=Page)
        self.bpm_page = BPMPage(self.mock_page)

    def test_safe_extract_columns_with_no_parent_row(self, caplog):
        """Test safe extraction when no parent row is provided."""
        with caplog.at_level(logging.WARNING):
            result = self.bpm_page._safe_extract_columns(None)
        
        assert result == []
        assert "No parent row provided for safe column extraction" in caplog.text

    def test_safe_extract_columns_with_locator_failure(self, caplog):
        """Test safe extraction when cell locator fails."""
        mock_parent_row = Mock()
        mock_parent_row.locator.side_effect = Exception("Locator failed")
        
        with caplog.at_level(logging.ERROR):
            result = self.bpm_page._safe_extract_columns(mock_parent_row)
        
        assert result == []
        assert "Failed to locate table cells in parent row" in caplog.text

    def test_safe_extract_columns_with_no_cells(self, caplog):
        """Test safe extraction when no cells are found."""
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_cells.count.return_value = 0
        mock_parent_row.locator.return_value = mock_cells
        
        with caplog.at_level(logging.WARNING):
            result = self.bpm_page._safe_extract_columns(mock_parent_row)
        
        assert result == []
        assert "No cells found in result row during safe extraction" in caplog.text

    def test_safe_extract_columns_successful_extraction(self, caplog):
        """Test safe extraction with successful column extraction."""
        mock_parent_row = Mock()
        mock_cells = Mock()
        mock_cells.count.return_value = 3
        
        # Mock three cells with different content
        mock_cells.nth.side_effect = [
            Mock(inner_text=Mock(return_value="text1")),
            Mock(inner_text=Mock(return_value="25")),
            Mock(inner_text=Mock(return_value="text3"))
        ]
        mock_parent_row.locator.return_value = mock_cells
        
        with caplog.at_level(logging.INFO):
            result = self.bpm_page._safe_extract_columns(mock_parent_row)
        
        assert len(result) == 3
        assert result[0].value == "text1"
        assert result[0].position == 1
        assert result[1].value == "25"
        assert result[1].position == 2
        assert result[1].is_numeric is True
        assert result[1].numeric_value == 25
        assert result[2].value == "text3"
        assert result[2].position == 3
        assert "Successfully extracted data from all 3 columns" in caplog.text


class TestHandleExtractionFailure:
    """Test the _handle_extraction_failure method for fallback scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=Page)
        self.bpm_page = BPMPage(self.mock_page)

    def test_handle_extraction_failure_successful_fallback(self, caplog):
        """Test extraction failure handler with successful fallback."""
        test_number = "12345"
        test_error = Exception("Original extraction failed")
        
        # Mock successful element finding and fallback extraction
        mock_element = Mock()
        mock_element.count.return_value = 1
        mock_element.first = Mock()
        mock_parent_row = Mock()
        mock_element.first.locator.return_value = mock_parent_row
        self.mock_page.locator.return_value = mock_element
        
        # Mock successful fallback extraction
        with patch.object(self.bpm_page, '_fallback_to_original_extraction', return_value=("Col4", "ColLast")):
            with caplog.at_level(logging.INFO):
                result = self.bpm_page._handle_extraction_failure(test_number, test_error)
        
        assert isinstance(result, BPMSearchResult)
        assert result.fourth_column == "Col4"
        assert result.last_column == "ColLast"
        assert result.second_to_last_column == "ExtractionFailed"
        assert result.environment == "unknown"
        assert result.transaction_found is True
        assert "Fallback extraction successful, returning partial data" in caplog.text

    def test_handle_extraction_failure_element_not_found(self, caplog):
        """Test extraction failure handler when element is not found during fallback."""
        test_number = "12345"
        test_error = Exception("Original extraction failed")
        
        # Mock element not found
        mock_element = Mock()
        mock_element.count.return_value = 0
        self.mock_page.locator.return_value = mock_element
        
        with caplog.at_level(logging.WARNING):
            result = self.bpm_page._handle_extraction_failure(test_number, test_error)
        
        assert isinstance(result, BPMSearchResult)
        assert result.fourth_column == "NotFound"
        assert result.last_column == "NotFound"
        assert result.transaction_found is False
        assert "Element not found during fallback extraction" in caplog.text


class TestErrorHandlingIntegration:
    """Test integration of error handling with main methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_page = Mock(spec=Page)
        self.bpm_page = BPMPage(self.mock_page)

    def test_graceful_degradation_maintains_basic_functionality(self, caplog):
        """Test that graceful degradation maintains basic functionality when enhanced features fail."""
        test_number = "12345"
        
        # Mock element found
        mock_element = Mock()
        mock_element.count.return_value = 1
        mock_element.first = Mock()
        mock_parent_row = Mock()
        mock_element.first.locator.return_value = mock_parent_row
        self.mock_page.locator.return_value = mock_element
        
        # Mock enhanced extraction to fail but fallback to succeed
        with patch.object(self.bpm_page, '_extract_all_columns', side_effect=Exception("Enhanced failed")):
            with patch.object(self.bpm_page, '_fallback_to_original_extraction', return_value=("BasicCol4", "BasicColLast")):
                result = self.bpm_page.look_for_number(test_number)
        
        # Should still return basic functionality
        assert result == ("BasicCol4", "BasicColLast")
        assert "Enhanced extraction failed" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])