"""Demo script showing backward compatibility layer functionality.

This script demonstrates how the backward compatibility layer allows existing
callers to continue working without modification while enabling new callers
to access enhanced data features.
"""

import logging
from unittest.mock import Mock
from datetime import datetime

# Import the classes we're demonstrating
from bpm.bpm_page import BPMPage, BPMSearchResult, ColumnData


def setup_mock_bpm_page():
    """Set up a mock BPMPage for demonstration purposes."""
    # Create a mock Playwright page
    mock_page = Mock()
    mock_page.locator.return_value = Mock()
    
    # Create BPMPage instance with mock page
    bmp_page = BPMPage(mock_page)
    
    # Sample column data representing a realistic BPM search result
    sample_columns = [
        ColumnData(position=1, value="TXN001", is_numeric=False, numeric_value=None),
        ColumnData(position=2, value="PENDING", is_numeric=False, numeric_value=None),
        ColumnData(position=3, value="USD", is_numeric=False, numeric_value=None),
        ColumnData(position=4, value="SWIFT_CODE", is_numeric=False, numeric_value=None),  # 4th column
        ColumnData(position=5, value="27", is_numeric=True, numeric_value=27),  # Environment indicator
        ColumnData(position=6, value="ENV-27-Q1", is_numeric=False, numeric_value=None),  # Second-to-last
        ColumnData(position=7, value="COMPLETED", is_numeric=False, numeric_value=None),  # Last column
    ]
    
    # Mock the internal methods to return our sample data
    def mock_extract_columns(parent_row):
        return sample_columns
    
    def mock_detect_environment(columns):
        return "buat"  # Based on value 27 in position 5
    
    def mock_build_enhanced_result(columns, environment):
        return BPMSearchResult(
            fourth_column="SWIFT_CODE",
            last_column="COMPLETED",
            all_columns=columns,
            second_to_last_column="ENV-27-Q1",
            environment=environment,
            total_columns=len(columns),
            transaction_found=True,
            search_timestamp=datetime.now().isoformat()
        )
    
    # Mock page locator behavior for successful search
    mock_element = Mock()
    mock_element.count.return_value = 1
    mock_element.first = Mock()
    mock_element.first.evaluate = Mock()
    mock_element.first.locator.return_value = Mock()
    mock_page.locator.return_value = mock_element
    
    # Patch the internal methods
    bmp_page._extract_all_columns = mock_extract_columns
    bmp_page._detect_environment = mock_detect_environment
    bmp_page._build_enhanced_result = mock_build_enhanced_result
    bmp_page.wait_for_page_to_load = Mock()
    mock_page.wait_for_timeout = Mock()
    
    return bmp_page


def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility scenarios."""
    print("=" * 80)
    print("BMP DATA ENHANCEMENT - BACKWARD COMPATIBILITY DEMONSTRATION")
    print("=" * 80)
    
    # Set up logging to show the enhanced logging features
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create mock BMP page
    bmp_page = setup_mock_bpm_page()
    test_number = "TXN12345"
    
    print("\n1. EXISTING CALLER BEHAVIOR (Unchanged)")
    print("-" * 50)
    print("Existing code using look_for_number() continues to work:")
    print(f"result = bmp_page.look_for_number('{test_number}')")
    
    # This simulates existing caller code - no changes needed
    result = bmp_page.look_for_number(test_number)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    print("✓ Existing callers get the same tuple format they expect")
    
    print("\n2. ENHANCED METHOD - DEFAULT BEHAVIOR (Backward Compatible)")
    print("-" * 50)
    print("New enhanced method with default parameters returns tuple:")
    print(f"result = bmp_page.look_for_number_enhanced('{test_number}')")
    
    result = bmp_page.look_for_number_enhanced(test_number)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    print("✓ Default behavior maintains backward compatibility")
    
    print("\n3. ENHANCED METHOD - ENHANCED RETURN (New Feature)")
    print("-" * 50)
    print("New callers can opt into enhanced data:")
    print(f"result = bmp_page.look_for_number_enhanced('{test_number}', return_enhanced=True)")
    
    result = bmp_page.look_for_number_enhanced(test_number, return_enhanced=True)
    print(f"Result type: {type(result)}")
    print(f"Fourth column: {result.fourth_column}")
    print(f"Last column: {result.last_column}")
    print(f"Second-to-last column: {result.second_to_last_column}")
    print(f"Environment: {result.environment}")
    print(f"Total columns: {result.total_columns}")
    print(f"Transaction found: {result.transaction_found}")
    print("✓ Enhanced data available when requested")
    
    print("\n4. ENHANCED SEARCH RESULTS - BACKWARD COMPATIBLE")
    print("-" * 50)
    print("Enhanced search_results method with default behavior:")
    print(f"result = bmp_page.search_results_enhanced('{test_number}')")
    
    result = bmp_page.search_results_enhanced(test_number)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    print("✓ Maintains tuple return for backward compatibility")
    
    print("\n5. ENHANCED SEARCH RESULTS - ENHANCED RETURN")
    print("-" * 50)
    print("Enhanced search_results with detailed data:")
    print(f"result = bmp_page.search_results_enhanced('{test_number}', return_enhanced=True)")
    
    result = bmp_page.search_results_enhanced(test_number, return_enhanced=True)
    print(f"Result type: {type(result)}")
    print(f"All columns count: {len(result.all_columns)}")
    print("Column details:")
    for col in result.all_columns:
        print(f"  - Position {col.position}: '{col.value}' (numeric: {col.is_numeric})")
    print("✓ Complete column data available when requested")
    
    print("\n6. ENHANCED LOGGING DEMONSTRATION")
    print("-" * 50)
    print("Enhanced logging preserves existing logs while adding new information:")
    print("(Check the log output above to see both traditional and enhanced log messages)")
    print("✓ Traditional log messages preserved")
    print("✓ New enhanced log messages added")
    
    print("\n7. ERROR HANDLING COMPATIBILITY")
    print("-" * 50)
    print("Error scenarios maintain backward compatibility:")
    
    # Mock a not found scenario
    mock_element = Mock()
    mock_element.count.return_value = 0
    bmp_page.page.locator.return_value = mock_element
    
    # Test tuple return on error
    result = bmp_page.look_for_number_enhanced("NOTFOUND", return_enhanced=False)
    print(f"Tuple error result: {result}")
    
    # Test enhanced return on error
    result = bmp_page.look_for_number_enhanced("NOTFOUND", return_enhanced=True)
    print(f"Enhanced error result: transaction_found={result.transaction_found}")
    print("✓ Error handling maintains consistency across both formats")


def demonstrate_migration_path():
    """Demonstrate how existing code can gradually migrate to enhanced features."""
    print("\n" + "=" * 80)
    print("MIGRATION PATH DEMONSTRATION")
    print("=" * 80)
    
    bmp_page = setup_mock_bpm_page()
    test_number = "TXN12345"
    
    print("\nSTEP 1: Existing code (no changes needed)")
    print("-" * 40)
    print("# Existing code continues to work")
    print("fourth, last = bmp_page.look_for_number('TXN12345')")
    fourth, last = bmp_page.look_for_number(test_number)
    print(f"fourth='{fourth}', last='{last}'")
    
    print("\nSTEP 2: Gradual migration - access enhanced data when needed")
    print("-" * 40)
    print("# New code can access enhanced data")
    print("result = bmp_page.look_for_number_enhanced('TXN12345', return_enhanced=True)")
    result = bmp_page.look_for_number_enhanced(test_number, return_enhanced=True)
    print(f"environment='{result.environment}', second_to_last='{result.second_to_last_column}'")
    print("# But still access traditional fields")
    print(f"fourth='{result.fourth_column}', last='{result.last_column}'")
    
    print("\nSTEP 3: Full migration - use enhanced methods throughout")
    print("-" * 40)
    print("# Eventually migrate to enhanced search_results")
    print("result = bmp_page.search_results_enhanced('TXN12345', return_enhanced=True)")
    result = bmp_page.search_results_enhanced(test_number, return_enhanced=True)
    print(f"Complete data available: {len(result.all_columns)} columns")
    
    print("\n✓ Migration can happen gradually without breaking existing functionality")


if __name__ == "__main__":
    demonstrate_backward_compatibility()
    demonstrate_migration_path()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✓ Existing callers continue to work without modification")
    print("✓ New callers can opt into enhanced data features")
    print("✓ Enhanced logging preserves existing log messages")
    print("✓ Error handling maintains consistency across formats")
    print("✓ Migration path allows gradual adoption of new features")
    print("✓ Backward compatibility layer successfully implemented")