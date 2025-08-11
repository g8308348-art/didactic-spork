"""Unit tests for numeric value parsing functionality in BPM page."""

import unittest
import sys
import os
from unittest.mock import Mock

# Add the bpm directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bpm'))

from bpm_page import BPMPage


class TestNumericValueParsing(unittest.TestCase):
    """Test cases for _parse_numeric_value method."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock page object for BPMPage initialization
        mock_page = Mock()
        self.bmp_page = BPMPage(mock_page)

    def test_parse_pure_integer_strings(self):
        """Test parsing of pure integer strings."""
        test_cases = [
            ("25", True, 25),
            ("0", True, 0),
            ("123", True, 123),
            ("999", True, 999),
            ("1", True, 1),
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_negative_numbers(self):
        """Test parsing of negative numbers."""
        test_cases = [
            ("-25", True, -25),
            ("-1", True, -1),
            ("-999", True, -999),
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_decimal_numbers(self):
        """Test parsing of decimal numbers (should extract integer part)."""
        test_cases = [
            ("25.5", True, 25),
            ("27.9", True, 27),
            ("0.5", True, 0),
            ("123.456", True, 123),
            ("-25.5", True, -25),
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_hyphenated_formats(self):
        """Test parsing of hyphenated formats like '25-Q1'."""
        test_cases = [
            ("25-Q1", True, 25),
            ("27-UAT", True, 27),
            ("29-PROD", True, 29),
            ("1-TEST", True, 1),
            ("123-ENV", True, 123),
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_mixed_text_with_numbers(self):
        """Test parsing of mixed text containing numbers."""
        test_cases = [
            ("ENV-27", True, 27),
            ("PACS.008", True, 8),  # Should extract 8 from PACS.008
            ("TEST123", True, 123),
            ("25TEST", True, 25),
            ("ABC25DEF", True, 25),
            ("VERSION2.5", True, 2),  # Should extract first number found (2 from VERSION2.5)
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_no_numeric_values(self):
        """Test parsing of text with no numeric values."""
        test_cases = [
            ("ABC", False, None),
            ("TEST", False, None),
            ("REGULAR", False, None),
            ("EUR", False, None),
            ("SUCCESS", False, None),
            ("", False, None),
            ("   ", False, None),
            ("!@#$%", False, None),
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_edge_cases(self):
        """Test parsing of edge cases and special scenarios."""
        test_cases = [
            # Empty and None cases
            (None, False, None),
            ("", False, None),
            ("   ", False, None),
            
            # Multiple numbers (should return first found)
            ("25-Q1-27", True, 25),
            ("ABC123DEF456", True, 123),
            
            # Numbers with special characters
            ("25@Q1", True, 25),
            ("ENV#27", True, 27),
            ("TEST_25_END", True, 25),
            
            # Leading/trailing whitespace
            ("  25  ", True, 25),
            ("\t27\n", True, 27),
            
            # Complex formats
            ("2025-08-06", True, 2025),
            ("10:57:32", True, 10),
            ("PF2EFBA2200914", True, 2),  # Should extract first number
        ]
        
        for text, expected_is_numeric, expected_value in test_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_environment_detection_values(self):
        """Test parsing values specifically relevant for environment detection."""
        # BUAT range values (25-29)
        buat_test_cases = [
            ("25", True, 25),
            ("26", True, 26),
            ("27", True, 27),
            ("28", True, 28),
            ("29", True, 29),
            ("25-Q1", True, 25),
            ("27-UAT", True, 27),
            ("ENV-29", True, 29),
        ]
        
        for text, expected_is_numeric, expected_value in buat_test_cases:
            with self.subTest(text=text, environment="buat"):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)
                # Verify it's in BUAT range
                self.assertIn(numeric_value, range(25, 30))

        # UAT range values (outside 25-29)
        uat_test_cases = [
            ("24", True, 24),
            ("30", True, 30),
            ("1", True, 1),
            ("100", True, 100),
            ("22-Q1", True, 22),
            ("31-PROD", True, 31),
        ]
        
        for text, expected_is_numeric, expected_value in uat_test_cases:
            with self.subTest(text=text, environment="uat"):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)
                # Verify it's outside BUAT range
                self.assertNotIn(numeric_value, range(25, 30))

    def test_parse_real_world_data_examples(self):
        """Test parsing with real-world data examples from the HTML screenshot."""
        real_world_cases = [
            # From the HTML screenshot data
            ("DEH", False, None),
            ("PF2EFBA2200914", True, 2),  # Should extract first number
            ("2025-08-06 10:57:32", True, 2025),  # Should extract first number
            ("BusinessResponseProcessed", False, None),
            ("2025/06/05", True, 2025),
            ("EUR", False, None),
            ("REGULAR", False, None),
            ("PACS.008", True, 8),  # Should extract 8
            ("SUCCESS", False, None),
            
            # Additional realistic examples
            ("MTEX-DATAGRID-THEAD", False, None),
            ("CLEARFIX", False, None),
            ("116.4px", True, 116),
            ("291.1px", True, 291),
            ("58.1px", True, 58),
        ]
        
        for text, expected_is_numeric, expected_value in real_world_cases:
            with self.subTest(text=text):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

    def test_parse_invalid_input_types(self):
        """Test parsing with invalid input types."""
        invalid_inputs = [
            123,  # Integer instead of string
            [],   # List
            {},   # Dictionary
            True, # Boolean
        ]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input=invalid_input):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(invalid_input)
                self.assertFalse(is_numeric)
                self.assertIsNone(numeric_value)

    def test_parse_performance_edge_cases(self):
        """Test parsing with performance-related edge cases."""
        # Very long strings
        long_string = "A" * 1000 + "25" + "B" * 1000
        is_numeric, numeric_value = self.bmp_page._parse_numeric_value(long_string)
        self.assertTrue(is_numeric)
        self.assertEqual(numeric_value, 25)
        
        # String with many numbers
        many_numbers = "1-2-3-4-5-6-7-8-9-10-11-12-13-14-15"
        is_numeric, numeric_value = self.bmp_page._parse_numeric_value(many_numbers)
        self.assertTrue(is_numeric)
        self.assertEqual(numeric_value, 1)  # Should return first number found

    def test_parse_regex_pattern_coverage(self):
        """Test that all regex patterns are working correctly."""
        # Test word boundary pattern
        word_boundary_cases = [
            ("word25word", True, 25),
            ("25word", True, 25),
            ("word25", True, 25),
        ]
        
        for text, expected_is_numeric, expected_value in word_boundary_cases:
            with self.subTest(text=text, pattern="word_boundary"):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

        # Test start of string pattern
        start_cases = [
            ("25-something", True, 25),
            ("123abc", True, 123),
        ]
        
        for text, expected_is_numeric, expected_value in start_cases:
            with self.subTest(text=text, pattern="start_of_string"):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)

        # Test end of string pattern
        end_cases = [
            ("something-25", True, 25),
            ("abc123", True, 123),
        ]
        
        for text, expected_is_numeric, expected_value in end_cases:
            with self.subTest(text=text, pattern="end_of_string"):
                is_numeric, numeric_value = self.bmp_page._parse_numeric_value(text)
                self.assertEqual(is_numeric, expected_is_numeric)
                self.assertEqual(numeric_value, expected_value)


if __name__ == '__main__':
    unittest.main()