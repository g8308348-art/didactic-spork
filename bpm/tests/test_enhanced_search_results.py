"""
Unit tests for enhanced search_results method functionality.

This module tests the enhanced search_results method to ensure it properly:
- Supports the new return_enhanced parameter
- Returns enhanced BPMSearchResult when requested
- Maintains backward compatibility with tuple return
- Integrates enhanced logging for second-to-last column and environment detection
- Preserves existing error handling behavior
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from bpm.bpm_page import BPMPage, BPMSearchResult, ColumnData


class TestEnhancedSearchResults:
    """Test suite for enhanced search_results method functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_page = Mock()
        self.bmp_page = BPMPage(self.mock_page)
        
        # Mock the page timeout and load methods
        self.mock_page.wait_for_timeout = Mock()
        self.bmp_page.wait_for_page_to_load = Mock()

    def test_search_results_backward_compatibility_default(self):
        """Test that search_results maintains backward compatibility by default."""
        # Arrange
        test_number = "12345"
        expected_fourth = "TestFourth"
        expected_last = "TestLast"
        
        # Mock the original look_for_number method
        self.bmp_page.look_for_number = Mock(return_value=(expected_fourth, expected_last))
        
        # Act
        result = self.bmp_page.search_results(test_number)
        
        # Assert
        assert isinstance(result, tuple)
        assert result == (expected_fourth, expected_last)
        assert len(result) == 2
        
        # Verify original method was called
        self.bmp_page.look_for_number.assert_called_once_with(test_number)
        
        # Verify page preparation methods were called
        self.mock_page.wait_for_timeout.assert_called_once_with(2000)
        self.bmp_page.wait_for_page_to_load.assert_called_once()

    def test_search_results_backward_compatibility_explicit_false(self):
        """Test that search_results returns tuple when return_enhanced=False."""
        # Arrange
        test_number = "67890"
        expected_fourth = "ExplicitFourth"
        expected_last = "ExplicitLast"
        
        # Mock the original look_for_number method
        self.bmp_page.look_for_number = Mock(return_value=(expected_fourth, expected_last))
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=False)
        
        # Assert
        assert isinstance(result, tuple)
        assert result == (expected_fourth, expected_last)
        
        # Verify original method was called
        self.bmp_page.look_for_number.assert_called_once_with(test_number)

    def test_search_results_enhanced_return_true(self):
        """Test that search_results returns BPMSearchResult when return_enhanced=True."""
        # Arrange
        test_number = "54321"
        mock_columns = [
            ColumnData(1, "Col1", False, None),
            ColumnData(2, "Col2", False, None),
            ColumnData(3, "Col3", False, None),
            ColumnData(4, "Col4", False, None),
            ColumnData(5, "Col5", True, 27),
            ColumnData(6, "Col6", False, None)
        ]
        
        expected_result = BPMSearchResult(
            fourth_column="Col4",
            last_column="Col6",
            all_columns=mock_columns,
            second_to_last_column="Col5",
            environment="buat",
            total_columns=6,
            transaction_found=True,
            search_timestamp="2024-01-01T12:00:00"
        )
        
        # Mock the enhanced look_for_number method
        self.bmp_page.look_for_number_enhanced = Mock(return_value=expected_result)
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        assert isinstance(result, BPMSearchResult)
        assert result == expected_result
        assert result.fourth_column == "Col4"
        assert result.last_column == "Col6"
        assert result.second_to_last_column == "Col5"
        assert result.environment == "buat"
        assert result.total_columns == 6
        assert result.transaction_found is True
        
        # Verify enhanced method was called
        self.bmp_page.look_for_number_enhanced.assert_called_once_with(test_number, return_enhanced=True)

    @patch('bpm.bpm_page.logging')
    def test_search_results_enhanced_logging(self, mock_logging):
        """Test that enhanced search_results includes proper logging for new fields."""
        # Arrange
        test_number = "11111"
        mock_result = BPMSearchResult(
            fourth_column="LogFourth",
            last_column="LogLast",
            all_columns=[],
            second_to_last_column="LogSecondLast",
            environment="uat",
            total_columns=8,
            transaction_found=True,
            search_timestamp="2024-01-01T12:00:00"
        )
        
        self.bmp_page.look_for_number_enhanced = Mock(return_value=mock_result)
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        assert result == mock_result
        
        # Verify enhanced logging was called with correct values
        expected_calls = [
            (("4th Column Value: %s", "LogFourth"),),
            (("Last Column Value: %s", "LogLast"),),
            (("Second-to-Last Column Value: %s", "LogSecondLast"),),
            (("Environment Detected: %s", "uat"),),
            (("Total Columns: %d", 8),)
        ]
        
        # Check that all expected log calls were made
        actual_calls = [call.args for call in mock_logging.info.call_args_list]
        for expected_call_args in expected_calls:
            assert expected_call_args[0] in actual_calls

    def test_search_results_error_handling_backward_compatible(self):
        """Test that error handling maintains backward compatibility."""
        # Arrange
        test_number = "error_case"
        
        # Mock look_for_number to raise an exception
        self.bmp_page.look_for_number = Mock(side_effect=Exception("Test error"))
        
        # Act
        result = self.bmp_page.search_results(test_number)
        
        # Assert
        assert isinstance(result, tuple)
        assert result == ("NotFound", "NotFound")

    def test_search_results_error_handling_enhanced(self):
        """Test that error handling returns proper BPMSearchResult when enhanced."""
        # Arrange
        test_number = "enhanced_error"
        
        # Mock the _build_not_found_result method
        expected_not_found = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=[],
            second_to_last_column="NotFound",
            environment="unknown",
            total_columns=0,
            transaction_found=False,
            search_timestamp="2024-01-01T12:00:00"
        )
        
        self.bmp_page.look_for_number_enhanced = Mock(side_effect=Exception("Enhanced error"))
        self.bmp_page._build_not_found_result = Mock(return_value=expected_not_found)
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        assert isinstance(result, BPMSearchResult)
        assert result == expected_not_found
        assert result.transaction_found is False
        
        # Verify _build_not_found_result was called
        self.bmp_page._build_not_found_result.assert_called_once()

    def test_search_results_unexpected_return_type_handling(self):
        """Test handling of unexpected return type from look_for_number_enhanced."""
        # Arrange
        test_number = "unexpected_type"
        
        # Mock look_for_number_enhanced to return unexpected type
        self.bmp_page.look_for_number_enhanced = Mock(return_value="unexpected_string")
        
        expected_not_found = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=[],
            second_to_last_column="NotFound",
            environment="unknown",
            total_columns=0,
            transaction_found=False,
            search_timestamp="2024-01-01T12:00:00"
        )
        
        self.bmp_page._build_not_found_result = Mock(return_value=expected_not_found)
        
        # Act
        result = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert
        assert isinstance(result, BPMSearchResult)
        assert result == expected_not_found
        
        # Verify _build_not_found_result was called due to unexpected type
        self.bmp_page._build_not_found_result.assert_called_once()

    @patch('bpm.bpm_page.logging')
    def test_search_results_error_logging(self, mock_logging):
        """Test that errors are properly logged in enhanced search_results."""
        # Arrange
        test_number = "logging_error"
        test_error = Exception("Test logging error")
        
        # Mock to raise exception
        self.bmp_page.look_for_number = Mock(side_effect=test_error)
        
        # Act
        result = self.bmp_page.search_results(test_number)
        
        # Assert
        assert result == ("NotFound", "NotFound")
        
        # Verify error was logged
        mock_logging.error.assert_called_once_with("Error in search_results: %s", test_error)

    def test_search_results_page_preparation_calls(self):
        """Test that page preparation methods are called correctly."""
        # Arrange
        test_number = "prep_test"
        
        self.bmp_page.look_for_number = Mock(return_value=("Fourth", "Last"))
        
        # Act
        self.bmp_page.search_results(test_number)
        
        # Assert page preparation methods were called
        self.mock_page.wait_for_timeout.assert_called_once_with(2000)
        self.bmp_page.wait_for_page_to_load.assert_called_once()

    def test_search_results_integration_with_existing_methods(self):
        """Test integration between enhanced search_results and existing helper methods."""
        # Arrange
        test_number = "integration_test"
        
        # Create realistic mock data
        mock_columns = [
            ColumnData(1, "TXN123", False, None),
            ColumnData(2, "PENDING", False, None),
            ColumnData(3, "USD", False, None),
            ColumnData(4, "INTEGRATION_FOURTH", False, None),
            ColumnData(5, "ENV-25", True, 25),
            ColumnData(6, "INTEGRATION_LAST", False, None)
        ]
        
        enhanced_result = BPMSearchResult(
            fourth_column="INTEGRATION_FOURTH",
            last_column="INTEGRATION_LAST",
            all_columns=mock_columns,
            second_to_last_column="ENV-25",
            environment="buat",
            total_columns=6,
            transaction_found=True,
            search_timestamp=datetime.now().isoformat()
        )
        
        # Mock the enhanced method
        self.bmp_page.look_for_number_enhanced = Mock(return_value=enhanced_result)
        
        # Mock the backward compatible method as well
        self.bmp_page.look_for_number = Mock(return_value=("INTEGRATION_FOURTH", "INTEGRATION_LAST"))
        
        # Act - Test both return formats
        tuple_result = self.bmp_page.search_results(test_number, return_enhanced=False)
        enhanced_result_returned = self.bmp_page.search_results(test_number, return_enhanced=True)
        
        # Assert backward compatibility
        assert isinstance(tuple_result, tuple)
        assert tuple_result == ("INTEGRATION_FOURTH", "INTEGRATION_LAST")
        
        # Assert enhanced functionality
        assert isinstance(enhanced_result_returned, BPMSearchResult)
        assert enhanced_result_returned.environment == "buat"
        assert enhanced_result_returned.second_to_last_column == "ENV-25"
        assert enhanced_result_returned.total_columns == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])