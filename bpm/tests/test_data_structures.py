"""Unit tests for enhanced BMP data structures."""

import unittest
from datetime import datetime
from bpm.bpm_page import ColumnData, BPMSearchResult


class TestColumnData(unittest.TestCase):
    """Test cases for ColumnData dataclass."""

    def test_column_data_creation_basic(self):
        """Test basic ColumnData creation with required fields."""
        column = ColumnData(position=1, value="test_value")
        
        self.assertEqual(column.position, 1)
        self.assertEqual(column.value, "test_value")
        self.assertFalse(column.is_numeric)
        self.assertIsNone(column.numeric_value)

    def test_column_data_creation_with_numeric(self):
        """Test ColumnData creation with numeric fields."""
        column = ColumnData(
            position=2, 
            value="25", 
            is_numeric=True, 
            numeric_value=25
        )
        
        self.assertEqual(column.position, 2)
        self.assertEqual(column.value, "25")
        self.assertTrue(column.is_numeric)
        self.assertEqual(column.numeric_value, 25)

    def test_column_data_str_representation(self):
        """Test string representation of ColumnData."""
        column = ColumnData(position=3, value="test_data")
        expected_str = "Col3: test_data"
        
        self.assertEqual(str(column), expected_str)

    def test_column_data_with_empty_value(self):
        """Test ColumnData with empty string value."""
        column = ColumnData(position=1, value="")
        
        self.assertEqual(column.position, 1)
        self.assertEqual(column.value, "")
        self.assertFalse(column.is_numeric)
        self.assertIsNone(column.numeric_value)

    def test_column_data_with_special_characters(self):
        """Test ColumnData with special characters in value."""
        special_value = "25-Q1@#$%"
        column = ColumnData(position=4, value=special_value)
        
        self.assertEqual(column.position, 4)
        self.assertEqual(column.value, special_value)

    def test_column_data_numeric_edge_cases(self):
        """Test ColumnData with edge case numeric values."""
        # Test with zero
        column_zero = ColumnData(position=1, value="0", is_numeric=True, numeric_value=0)
        self.assertEqual(column_zero.numeric_value, 0)
        
        # Test with negative number
        column_negative = ColumnData(position=2, value="-5", is_numeric=True, numeric_value=-5)
        self.assertEqual(column_negative.numeric_value, -5)


class TestBPMSearchResult(unittest.TestCase):
    """Test cases for BPMSearchResult dataclass."""

    def setUp(self):
        """Set up test data for BPMSearchResult tests."""
        self.sample_columns = [
            ColumnData(position=1, value="col1_data"),
            ColumnData(position=2, value="col2_data"),
            ColumnData(position=3, value="col3_data"),
            ColumnData(position=4, value="col4_data"),
            ColumnData(position=5, value="25", is_numeric=True, numeric_value=25),
            ColumnData(position=6, value="last_col_data")
        ]
        
        self.timestamp = datetime.now().isoformat()

    def test_bpm_search_result_creation_found(self):
        """Test BPMSearchResult creation for found transaction."""
        result = BPMSearchResult(
            fourth_column="col4_data",
            last_column="last_col_data",
            all_columns=self.sample_columns,
            second_to_last_column="25",
            environment="buat",
            total_columns=6,
            transaction_found=True,
            search_timestamp=self.timestamp
        )
        
        self.assertEqual(result.fourth_column, "col4_data")
        self.assertEqual(result.last_column, "last_col_data")
        self.assertEqual(result.second_to_last_column, "25")
        self.assertEqual(result.environment, "buat")
        self.assertEqual(result.total_columns, 6)
        self.assertTrue(result.transaction_found)
        self.assertEqual(result.search_timestamp, self.timestamp)
        self.assertEqual(len(result.all_columns), 6)

    def test_bmp_search_result_creation_not_found(self):
        """Test BPMSearchResult creation for not found transaction."""
        result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=[],
            second_to_last_column="NotFound",
            environment="unknown",
            total_columns=0,
            transaction_found=False,
            search_timestamp=self.timestamp
        )
        
        self.assertEqual(result.fourth_column, "NotFound")
        self.assertEqual(result.last_column, "NotFound")
        self.assertEqual(result.second_to_last_column, "NotFound")
        self.assertEqual(result.environment, "unknown")
        self.assertEqual(result.total_columns, 0)
        self.assertFalse(result.transaction_found)
        self.assertEqual(len(result.all_columns), 0)

    def test_bpm_search_result_to_dict_basic(self):
        """Test to_dict method with basic data."""
        result = BPMSearchResult(
            fourth_column="test_fourth",
            last_column="test_last",
            all_columns=[
                ColumnData(position=1, value="test1"),
                ColumnData(position=2, value="test2", is_numeric=True, numeric_value=25)
            ],
            second_to_last_column="test_second_last",
            environment="uat",
            total_columns=2,
            transaction_found=True,
            search_timestamp=self.timestamp
        )
        
        result_dict = result.to_dict()
        
        # Check main fields
        self.assertEqual(result_dict["fourth_column"], "test_fourth")
        self.assertEqual(result_dict["last_column"], "test_last")
        self.assertEqual(result_dict["second_to_last_column"], "test_second_last")
        self.assertEqual(result_dict["environment"], "uat")
        self.assertEqual(result_dict["total_columns"], 2)
        self.assertTrue(result_dict["transaction_found"])
        self.assertEqual(result_dict["search_timestamp"], self.timestamp)
        
        # Check all_columns structure
        self.assertIn("all_columns", result_dict)
        self.assertEqual(len(result_dict["all_columns"]), 2)
        
        # Check first column
        col1 = result_dict["all_columns"][0]
        self.assertEqual(col1["position"], 1)
        self.assertEqual(col1["value"], "test1")
        self.assertFalse(col1["is_numeric"])
        self.assertIsNone(col1["numeric_value"])
        
        # Check second column
        col2 = result_dict["all_columns"][1]
        self.assertEqual(col2["position"], 2)
        self.assertEqual(col2["value"], "test2")
        self.assertTrue(col2["is_numeric"])
        self.assertEqual(col2["numeric_value"], 25)

    def test_bpm_search_result_to_dict_empty_columns(self):
        """Test to_dict method with empty columns list."""
        result = BPMSearchResult(
            fourth_column="NotFound",
            last_column="NotFound",
            all_columns=[],
            second_to_last_column="NotFound",
            environment="unknown",
            total_columns=0,
            transaction_found=False,
            search_timestamp=self.timestamp
        )
        
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict["all_columns"], [])
        self.assertEqual(result_dict["total_columns"], 0)
        self.assertFalse(result_dict["transaction_found"])

    def test_bpm_search_result_environment_values(self):
        """Test BPMSearchResult with different environment values."""
        environments = ["buat", "uat", "unknown"]
        
        for env in environments:
            result = BPMSearchResult(
                fourth_column="test",
                last_column="test",
                all_columns=[],
                second_to_last_column="test",
                environment=env,
                total_columns=0,
                transaction_found=True,
                search_timestamp=self.timestamp
            )
            
            self.assertEqual(result.environment, env)
            self.assertEqual(result.to_dict()["environment"], env)

    def test_bpm_search_result_with_large_column_set(self):
        """Test BPMSearchResult with many columns."""
        large_column_set = [
            ColumnData(position=i, value=f"col_{i}_data", is_numeric=(i % 2 == 0), numeric_value=i if i % 2 == 0 else None)
            for i in range(1, 11)  # 10 columns
        ]
        
        result = BPMSearchResult(
            fourth_column="col_4_data",
            last_column="col_10_data",
            all_columns=large_column_set,
            second_to_last_column="col_9_data",
            environment="buat",
            total_columns=10,
            transaction_found=True,
            search_timestamp=self.timestamp
        )
        
        self.assertEqual(result.total_columns, 10)
        self.assertEqual(len(result.all_columns), 10)
        
        result_dict = result.to_dict()
        self.assertEqual(len(result_dict["all_columns"]), 10)
        
        # Verify structure of serialized columns
        for i, col_dict in enumerate(result_dict["all_columns"]):
            expected_position = i + 1
            self.assertEqual(col_dict["position"], expected_position)
            self.assertEqual(col_dict["value"], f"col_{expected_position}_data")
            self.assertEqual(col_dict["is_numeric"], expected_position % 2 == 0)
            if expected_position % 2 == 0:
                self.assertEqual(col_dict["numeric_value"], expected_position)
            else:
                self.assertIsNone(col_dict["numeric_value"])


class TestDataStructureValidation(unittest.TestCase):
    """Test cases for data structure validation and edge cases."""

    def test_column_data_type_validation(self):
        """Test that ColumnData handles different data types correctly."""
        # Test with integer position
        column = ColumnData(position=1, value="test")
        self.assertIsInstance(column.position, int)
        
        # Test with string value
        self.assertIsInstance(column.value, str)
        
        # Test with boolean is_numeric
        column_numeric = ColumnData(position=1, value="25", is_numeric=True)
        self.assertIsInstance(column_numeric.is_numeric, bool)

    def test_bpm_search_result_field_types(self):
        """Test that BPMSearchResult fields have correct types."""
        timestamp = datetime.now().isoformat()
        columns = [ColumnData(position=1, value="test")]
        
        result = BPMSearchResult(
            fourth_column="test",
            last_column="test",
            all_columns=columns,
            second_to_last_column="test",
            environment="buat",
            total_columns=1,
            transaction_found=True,
            search_timestamp=timestamp
        )
        
        self.assertIsInstance(result.fourth_column, str)
        self.assertIsInstance(result.last_column, str)
        self.assertIsInstance(result.all_columns, list)
        self.assertIsInstance(result.second_to_last_column, str)
        self.assertIsInstance(result.environment, str)
        self.assertIsInstance(result.total_columns, int)
        self.assertIsInstance(result.transaction_found, bool)
        self.assertIsInstance(result.search_timestamp, str)

    def test_serialization_consistency(self):
        """Test that to_dict serialization is consistent and reversible."""
        original_columns = [
            ColumnData(position=1, value="data1", is_numeric=False, numeric_value=None),
            ColumnData(position=2, value="25", is_numeric=True, numeric_value=25)
        ]
        
        timestamp = datetime.now().isoformat()
        
        original_result = BPMSearchResult(
            fourth_column="fourth",
            last_column="last",
            all_columns=original_columns,
            second_to_last_column="second_last",
            environment="buat",
            total_columns=2,
            transaction_found=True,
            search_timestamp=timestamp
        )
        
        # Serialize to dict
        serialized = original_result.to_dict()
        
        # Verify all fields are present
        expected_keys = {
            "fourth_column", "last_column", "second_to_last_column", 
            "environment", "total_columns", "transaction_found", 
            "search_timestamp", "all_columns"
        }
        self.assertEqual(set(serialized.keys()), expected_keys)
        
        # Verify column serialization
        self.assertEqual(len(serialized["all_columns"]), 2)
        
        col1_serialized = serialized["all_columns"][0]
        self.assertEqual(col1_serialized["position"], 1)
        self.assertEqual(col1_serialized["value"], "data1")
        self.assertFalse(col1_serialized["is_numeric"])
        self.assertIsNone(col1_serialized["numeric_value"])
        
        col2_serialized = serialized["all_columns"][1]
        self.assertEqual(col2_serialized["position"], 2)
        self.assertEqual(col2_serialized["value"], "25")
        self.assertTrue(col2_serialized["is_numeric"])
        self.assertEqual(col2_serialized["numeric_value"], 25)


if __name__ == '__main__':
    unittest.main()