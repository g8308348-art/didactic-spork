"""Demo script to showcase environment detection functionality."""

import sys
import os
from unittest.mock import Mock

# Add the bpm directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bpm'))

from bpm_page import BPMPage, ColumnData


def demo_environment_detection():
    """Demonstrate the environment detection functionality with various scenarios."""
    
    # Create a mock page object for BPMPage initialization
    mock_page = Mock()
    bmp_page = BPMPage(mock_page)
    
    print("=== BMP Environment Detection Demo ===\n")
    
    # Scenario 1: BUAT Environment Detection
    print("Scenario 1: BUAT Environment (values 25-29)")
    buat_columns = [
        ColumnData(position=1, value="TRANSACTION_REF", is_numeric=False, numeric_value=None),
        ColumnData(position=2, value="27-Q1", is_numeric=True, numeric_value=27),
        ColumnData(position=3, value="SUCCESS", is_numeric=False, numeric_value=None),
    ]
    
    environment = bmp_page._detect_environment(buat_columns)
    print(f"Columns: {[f'Col{col.position}: {col.value}' for col in buat_columns]}")
    print(f"Detected Environment: {environment}")
    print()
    
    # Scenario 2: UAT Environment Detection
    print("Scenario 2: UAT Environment (values outside 25-29)")
    uat_columns = [
        ColumnData(position=1, value="ENV-22", is_numeric=True, numeric_value=22),
        ColumnData(position=2, value="TRANSACTION_ID", is_numeric=False, numeric_value=None),
        ColumnData(position=3, value="PROCESSED", is_numeric=False, numeric_value=None),
    ]
    
    environment = bmp_page._detect_environment(uat_columns)
    print(f"Columns: {[f'Col{col.position}: {col.value}' for col in uat_columns]}")
    print(f"Detected Environment: {environment}")
    print()
    
    # Scenario 3: Unknown Environment (no numeric values)
    print("Scenario 3: Unknown Environment (no numeric values)")
    unknown_columns = [
        ColumnData(position=1, value="REFERENCE", is_numeric=False, numeric_value=None),
        ColumnData(position=2, value="STATUS", is_numeric=False, numeric_value=None),
        ColumnData(position=3, value="CURRENCY", is_numeric=False, numeric_value=None),
    ]
    
    environment = bmp_page._detect_environment(unknown_columns)
    print(f"Columns: {[f'Col{col.position}: {col.value}' for col in unknown_columns]}")
    print(f"Detected Environment: {environment}")
    print()
    
    # Scenario 4: First Match Wins (mixed values)
    print("Scenario 4: First Match Wins (UAT value comes before BUAT value)")
    mixed_columns = [
        ColumnData(position=1, value="TEXT", is_numeric=False, numeric_value=None),
        ColumnData(position=2, value="24", is_numeric=True, numeric_value=24),  # UAT - first numeric
        ColumnData(position=3, value="27", is_numeric=True, numeric_value=27),  # BUAT - second numeric
    ]
    
    environment = bmp_page._detect_environment(mixed_columns)
    print(f"Columns: {[f'Col{col.position}: {col.value}' for col in mixed_columns]}")
    print(f"Detected Environment: {environment} (first numeric value 24 determines UAT)")
    print()
    
    # Scenario 5: Realistic BPM Data
    print("Scenario 5: Realistic BPM Transaction Data")
    realistic_columns = [
        ColumnData(position=1, value="DEH", is_numeric=False, numeric_value=None),
        ColumnData(position=2, value="PF2EFBA2200914", is_numeric=True, numeric_value=2),
        ColumnData(position=3, value="2025-08-06 10:57:32", is_numeric=True, numeric_value=2025),
        ColumnData(position=4, value="BusinessResponseProcessed", is_numeric=False, numeric_value=None),
        ColumnData(position=5, value="EUR", is_numeric=False, numeric_value=None),
        ColumnData(position=6, value="REGULAR", is_numeric=False, numeric_value=None),
    ]
    
    environment = bmp_page._detect_environment(realistic_columns)
    print(f"Columns: {[f'Col{col.position}: {col.value}' for col in realistic_columns]}")
    print(f"Detected Environment: {environment} (first numeric value 2 determines UAT)")
    print()
    
    # Scenario 6: Boundary Value Testing
    print("Scenario 6: Boundary Value Testing")
    boundary_cases = [
        (24, "uat"),   # Just below BUAT range
        (25, "buat"),  # Lower boundary of BUAT range
        (29, "buat"),  # Upper boundary of BUAT range
        (30, "uat"),   # Just above BUAT range
    ]
    
    for value, expected in boundary_cases:
        columns = [ColumnData(position=1, value=str(value), is_numeric=True, numeric_value=value)]
        environment = bmp_page._detect_environment(columns)
        print(f"Value {value}: Expected {expected}, Got {environment} ✓" if environment == expected else f"Value {value}: Expected {expected}, Got {environment} ✗")
    
    print("\n=== Demo Complete ===")


if __name__ == '__main__':
    demo_environment_detection()