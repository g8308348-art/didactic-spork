"""Demonstration of enhanced BMP data structures."""

from datetime import datetime
from bpm.bpm_page import ColumnData, BPMSearchResult


def demo_column_data():
    """Demonstrate ColumnData usage."""
    print("=== ColumnData Demo ===")
    
    # Create sample columns
    columns = [
        ColumnData(position=1, value="TXN123"),
        ColumnData(position=2, value="USD"),
        ColumnData(position=3, value="1000.00"),
        ColumnData(position=4, value="PENDING"),
        ColumnData(position=5, value="25", is_numeric=True, numeric_value=25),
        ColumnData(position=6, value="COMPLETED")
    ]
    
    print("Sample columns:")
    for col in columns:
        print(f"  {col}")
    
    print(f"\nNumeric columns:")
    for col in columns:
        if col.is_numeric:
            print(f"  {col} -> numeric value: {col.numeric_value}")


def demo_bpm_search_result():
    """Demonstrate BPMSearchResult usage."""
    print("\n=== BPMSearchResult Demo ===")
    
    # Create sample columns
    sample_columns = [
        ColumnData(position=1, value="TXN456"),
        ColumnData(position=2, value="EUR"),
        ColumnData(position=3, value="2500.00"),
        ColumnData(position=4, value="APPROVED"),
        ColumnData(position=5, value="27-Q1", is_numeric=True, numeric_value=27),
        ColumnData(position=6, value="PROCESSED")
    ]
    
    # Create search result
    result = BPMSearchResult(
        fourth_column="APPROVED",
        last_column="PROCESSED",
        all_columns=sample_columns,
        second_to_last_column="27-Q1",
        environment="buat",
        total_columns=6,
        transaction_found=True,
        search_timestamp=datetime.now().isoformat()
    )
    
    print("Search Result:")
    print(f"  Fourth Column: {result.fourth_column}")
    print(f"  Last Column: {result.last_column}")
    print(f"  Second-to-Last Column: {result.second_to_last_column}")
    print(f"  Environment: {result.environment}")
    print(f"  Total Columns: {result.total_columns}")
    print(f"  Transaction Found: {result.transaction_found}")
    print(f"  Timestamp: {result.search_timestamp}")
    
    print(f"\nAll Columns ({len(result.all_columns)}):")
    for col in result.all_columns:
        print(f"  {col}")


def demo_json_serialization():
    """Demonstrate JSON serialization."""
    print("\n=== JSON Serialization Demo ===")
    
    # Create a simple result
    columns = [
        ColumnData(position=1, value="TEST123"),
        ColumnData(position=2, value="25", is_numeric=True, numeric_value=25)
    ]
    
    result = BPMSearchResult(
        fourth_column="NotFound",
        last_column="TEST123",
        all_columns=columns,
        second_to_last_column="25",
        environment="buat",
        total_columns=2,
        transaction_found=True,
        search_timestamp=datetime.now().isoformat()
    )
    
    # Convert to dictionary
    result_dict = result.to_dict()
    
    print("Serialized to dictionary:")
    import json
    print(json.dumps(result_dict, indent=2))


def demo_not_found_scenario():
    """Demonstrate not found scenario."""
    print("\n=== Not Found Scenario Demo ===")
    
    not_found_result = BPMSearchResult(
        fourth_column="NotFound",
        last_column="NotFound",
        all_columns=[],
        second_to_last_column="NotFound",
        environment="unknown",
        total_columns=0,
        transaction_found=False,
        search_timestamp=datetime.now().isoformat()
    )
    
    print("Not Found Result:")
    print(f"  Transaction Found: {not_found_result.transaction_found}")
    print(f"  Environment: {not_found_result.environment}")
    print(f"  Total Columns: {not_found_result.total_columns}")
    print(f"  All Columns: {not_found_result.all_columns}")


if __name__ == "__main__":
    demo_column_data()
    demo_bpm_search_result()
    demo_json_serialization()
    demo_not_found_scenario()
    
    print("\n=== Demo Complete ===")
    print("Enhanced data structures are ready for use!")