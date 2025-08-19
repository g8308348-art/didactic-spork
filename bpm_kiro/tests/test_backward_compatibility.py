"""Unit tests for backward compatibility layer in BPM data enhancement.

This module tests the backward compatibility functionality to ensure existing
callers continue to work without modification while new callers can opt into
enhanced data features.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import logging

# Import the classes we're testing
from bpm.bpm_page import BPMPage, BPMSearchResult, ColumnData


class TestBackwardCompatibility(unittest.TestCase):
    """Test cases for backward compatibility layer functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock Playwright page
        self.mock_page = Mock()
        self.mock_page.locator.return_value = Mock()
        
        # Create BPMPage instance with mock page
        self.bmp_page = BPMPage(self.mock_page)
        
        # Sample column data for testing
        self.sample_columns = [
            ColumnData(position=1, value="COL1", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="COL2", is_numeric=False, numeric_value=None),
            ColumnData(position=3, value="COL3", is_numeric=False, numeric_value=None),
            ColumnData(position=4, value="FOURTH", is_numeric=False, numeric_value=None),
            ColumnData(position=5, value="25", is_numeric=True, numeric_value=25),
            ColumnData(position=6, value="SECOND_LAST", is_numeric=False, numeric_value=None),
            ColumnData(position=7, value="LAST", is_numeric=False, numeric_value=None),
        ]

    def test_look_for_number_enhanced_returns_tuple_by_default(self):
        """Test that look_for_number_enhanced returns tuple by default for backward compatibility."""
        test_number = "12345"
        
        # Mock the internal methods to return sample data
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=self.sample_columns), \
             patch.object(self.bmp_page, '_detect_environment', return_value="buat"), \
             patch.object(self.bmp_page, '_build_enhanced_result') as mock_build:
            
            # Create a mock enhanced result
            mock_enhanced_result = BPMSearchResult(
                fourth_column="FOURTH",
                last_column="LAST",
                all_columns=self.sample_columns,
                second_to_last_column="SECOND_LAST",
                environment="buat",
                total_columns=7,
                transaction_found=True,
                search_timestamp=datetime.now().isoformat()
            )
            mock_build.return_value = mock_enhanced_result
            
            # Mock page locator behavior for successful search
            mock_element = Mock()
            mock_element.count.return_value = 1
            mock_element.first = Mock()
            mock_element.first.evaluate = Mock()
            mock_element.first.locator.return_value = Mock()
            self.mock_page.locator.return_value = mock_element
            
            # Test default behavior (should return tuple)
            result = self.bmp_page.look_for_number_enhanced(test_number)
            
            # Verify result is a tuple with expected values
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], "FOURTH")
            self.assertEqual(result[1], "LAST")

    def test_look_for_number_enhanced_returns_enhanced_when_requested(self):
        """Test that look_for_number_enhanced returns BPMSearchResult when return_enhanced=True."""
        test_number = "12345"
        
        # Mock the internal methods to return sample data
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=self.sample_columns), \
             patch.object(self.bmp_page, '_detect_environment', return_value="buat"), \
             patch.object(self.bmp_page, '_build_enhanced_result') as mock_build:
            
            # Create a mock enhanced result
            mock_enhanced_result = BPMSearchResult(
                fourth_column="FOURTH",
                last_column="LAST",
                all_columns=self.sample_columns,
                second_to_last_column="SECOND_LAST",
                environment="buat",
                total_columns=7,
                transaction_found=True,
                search_timestamp=datetime.now().isoformat()
            )
            mock_build.return_value = mock_enhanced_result
            
            # Mock page locator behavior for successful search
            mock_element = Mock()
            mock_element.count.return_value = 1
            mock_element.first = Mock()
            mock_element.first.evaluate = Mock()
            mock_element.first.locator.return_value = Mock()
            self.mock_page.locator.return_value = mock_element
            
            # Test enhanced return behavior
            result = self.bmp_page.look_for_number_enhanced(test_number, return_enhanced=True)
            
            # Verify result is BPMSearchResult with expected values
            self.assertIsInstance(result, BPMSearchResult)
            self.assertEqual(result.fourth_column, "FOURTH")
            self.assertEqual(result.last_column, "LAST")
            self.assertEqual(result.second_to_last_column, "SECOND_LAST")
            self.assertEqual(result.environment, "buat")
            self.assertEqual(result.total_columns, 7)
            self.assertTrue(result.transaction_found)

    def test_look_for_number_enhanced_fallback_behavior(self):
        """Test fallback behavior when enhanced extraction fails."""
        test_number = "12345"
        
        # Mock enhanced extraction to fail, fallback to succeed
        with patch.object(self.bmp_page, '_extract_all_columns', side_effect=Exception("Extraction failed")), \
             patch.object(self.bmp_page, '_fallback_to_original_extraction', return_value=("FALLBACK_FOURTH", "FALLBACK_LAST")):
            
            # Mock page locator behavior for successful search
            mock_element = Mock()
            mock_element.count.return_value = 1
            mock_element.first = Mock()
            mock_element.first.evaluate = Mock()
            mock_element.first.locator.return_value = Mock()
            self.mock_page.locator.return_value = mock_element
            
            # Test tuple return with fallback
            result = self.bmp_page.look_for_number_enhanced(test_number, return_enhanced=False)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0], "FALLBACK_FOURTH")
            self.assertEqual(result[1], "FALLBACK_LAST")
            
            # Test enhanced return with fallback
            enhanced_result = self.bmp_page.look_for_number_enhanced(test_number, return_enhanced=True)
            self.assertIsInstance(enhanced_result, BPMSearchResult)
            self.assertEqual(enhanced_result.fourth_column, "FALLBACK_FOURTH")
            self.assertEqual(enhanced_result.last_column, "FALLBACK_LAST")
            self.assertEqual(enhanced_result.second_to_last_column, "ExtractionFailed")
            self.assertEqual(enhanced_result.environment, "unknown")

    def test_look_for_number_enhanced_not_found_scenario(self):
        """Test behavior when number is not found."""
        test_number = "99999"
        
        # Mock page locator to return no elements
        mock_element = Mock()
        mock_element.count.return_value = 0
        self.mock_page.locator.return_value = mock_element
        
        # Test tuple return for not found
        result = self.bmp_page.look_for_number_enhanced(test_number, return_enhanced=False)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], "NotFound")
        self.assertEqual(result[1], "NotFound")
        
        # Test enhanced return for not found
        enhanced_result = self.bmp_page.look_for_number_enhanced(test_number, return_enhanced=True)
        self.assertIsInstance(enhanced_result, BPMSearchResult)
        self.assertEqual(enhanced_result.fourth_column, "NotFound")
        self.assertEqual(enhanced_result.last_column, "NotFound")
        self.assertEqual(enhanced_result.second_to_last_column, "NotFound")
        self.assertEqual(enhanced_result.environment, "unknown")
        self.assertFalse(enhanced_result.transaction_found)

    def test_search_results_enhanced_backward_compatibility(self):
        """Test that search_results_enhanced maintains backward compatibility."""
        test_number = "12345"
        
        # Mock the enhanced look_for_number method
        mock_enhanced_result = BPMSearchResult(
            fourth_column="SEARCH_FOURTH",
            last_column="SEARCH_LAST",
            all_columns=self.sample_columns,
            second_to_last_column="SEARCH_SECOND_LAST",
            environment="uat",
            total_columns=7,
            transaction_found=True,
            search_timestamp=datetime.now().isoformat()
        )
        
        with patch.object(self.bmp_page, 'look_for_number_enhanced', return_value=mock_enhanced_result), \
             patch.object(self.bmp_page, 'wait_for_page_to_load'):
            
            # Mock page timeout
            self.mock_page.wait_for_timeout = Mock()
            
            # Test default behavior (should return tuple)
            result = self.bmp_page.search_results_enhanced(test_number)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0], "SEARCH_FOURTH")
            self.assertEqual(result[1], "SEARCH_LAST")
            
            # Test enhanced return behavior
            enhanced_result = self.bmp_page.search_results_enhanced(test_number, return_enhanced=True)
            self.assertIsInstance(enhanced_result, BPMSearchResult)
            self.assertEqual(enhanced_result.fourth_column, "SEARCH_FOURTH")
            self.assertEqual(enhanced_result.last_column, "SEARCH_LAST")
            self.assertEqual(enhanced_result.environment, "uat")

    def test_search_results_enhanced_error_handling(self):
        """Test error handling in search_results_enhanced method."""
        test_number = "12345"
        
        # Mock methods to raise exception
        with patch.object(self.bmp_page, 'wait_for_page_to_load', side_effect=Exception("Page load failed")), \
             patch.object(self.bmp_page, '_build_not_found_result') as mock_not_found:
            
            mock_not_found_result = BPMSearchResult(
                fourth_column="NotFound",
                last_column="NotFound",
                all_columns=[],
                second_to_last_column="NotFound",
                environment="unknown",
                total_columns=0,
                transaction_found=False,
                search_timestamp=datetime.now().isoformat()
            )
            mock_not_found.return_value = mock_not_found_result
            
            # Mock page timeout
            self.mock_page.wait_for_timeout = Mock()
            
            # Test tuple return on error
            result = self.bmp_page.search_results_enhanced(test_number, return_enhanced=False)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0], "NotFound")
            self.assertEqual(result[1], "NotFound")
            
            # Test enhanced return on error
            enhanced_result = self.bmp_page.search_results_enhanced(test_number, return_enhanced=True)
            self.assertIsInstance(enhanced_result, BPMSearchResult)
            self.assertFalse(enhanced_result.transaction_found)

    @patch('bpm.bpm_page.logging')
    def test_enhanced_logging_preservation(self, mock_logging):
        """Test that enhanced logging preserves existing log messages while adding new ones."""
        test_number = "12345"
        
        # Mock the internal methods to return sample data
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=self.sample_columns), \
             patch.object(self.bmp_page, '_detect_environment', return_value="buat"), \
             patch.object(self.bmp_page, '_build_enhanced_result') as mock_build:
            
            # Create a mock enhanced result
            mock_enhanced_result = BPMSearchResult(
                fourth_column="LOG_FOURTH",
                last_column="LOG_LAST",
                all_columns=self.sample_columns,
                second_to_last_column="LOG_SECOND_LAST",
                environment="buat",
                total_columns=7,
                transaction_found=True,
                search_timestamp=datetime.now().isoformat()
            )
            mock_build.return_value = mock_enhanced_result
            
            # Mock page locator behavior for successful search
            mock_element = Mock()
            mock_element.count.return_value = 1
            mock_element.first = Mock()
            mock_element.first.evaluate = Mock()
            mock_element.first.locator.return_value = Mock()
            self.mock_page.locator.return_value = mock_element
            
            # Call the enhanced method
            self.bmp_page.look_for_number_enhanced(test_number, return_enhanced=True)
            
            # Verify that both traditional and enhanced logging occurred
            log_calls = [call[0][0] for call in mock_logging.info.call_args_list]
            
            # Check for traditional log messages (backward compatibility)
            self.assertTrue(any("4th Column Value:" in msg for msg in log_calls))
            self.assertTrue(any("Last Column Value:" in msg for msg in log_calls))
            
            # Check for new enhanced log messages
            self.assertTrue(any("Second-to-Last Column Value:" in msg for msg in log_calls))
            self.assertTrue(any("Environment Detected:" in msg for msg in log_calls))
            self.assertTrue(any("Total Columns:" in msg for msg in log_calls))

    def test_existing_callers_unchanged(self):
        """Test that existing callers using the original look_for_number method still work."""
        test_number = "12345"
        
        # Mock the internal methods used by the original look_for_number
        with patch.object(self.bmp_page, '_extract_all_columns', return_value=self.sample_columns), \
             patch.object(self.bmp_page, '_detect_environment', return_value="buat"), \
             patch.object(self.bmp_page, '_build_enhanced_result') as mock_build:
            
            # Create a mock enhanced result
            mock_enhanced_result = BPMSearchResult(
                fourth_column="ORIGINAL_FOURTH",
                last_column="ORIGINAL_LAST",
                all_columns=self.sample_columns,
                second_to_last_column="ORIGINAL_SECOND_LAST",
                environment="buat",
                total_columns=7,
                transaction_found=True,
                search_timestamp=datetime.now().isoformat()
            )
            mock_build.return_value = mock_enhanced_result
            
            # Mock page locator behavior for successful search
            mock_element = Mock()
            mock_element.count.return_value = 1
            mock_element.first = Mock()
            mock_element.first.evaluate = Mock()
            mock_element.first.locator.return_value = Mock()
            self.mock_page.locator.return_value = mock_element
            
            # Test that the original look_for_number method still returns a tuple
            result = self.bmp_page.look_for_number(test_number)
            
            # Verify result is still a tuple (backward compatibility maintained)
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], "ORIGINAL_FOURTH")
            self.assertEqual(result[1], "ORIGINAL_LAST")

    def test_original_search_results_unchanged(self):
        """Test that the original search_results method behavior is preserved."""
        test_number = "12345"
        
        # Mock the look_for_number method to return expected tuple
        with patch.object(self.bmp_page, 'look_for_number', return_value=("SEARCH_FOURTH", "SEARCH_LAST")), \
             patch.object(self.bmp_page, 'wait_for_page_to_load'):
            
            # Mock page timeout
            self.mock_page.wait_for_timeout = Mock()
            
            # Test that original search_results still works
            result = self.bmp_page.search_results(test_number)
            
            # Verify result is a tuple with expected values
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0], "SEARCH_FOURTH")
            self.assertEqual(result[1], "SEARCH_LAST")


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    # Run the tests
    unittest.main()