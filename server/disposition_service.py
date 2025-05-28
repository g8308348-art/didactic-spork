import os
import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from main_logic import process_transaction, OUTPUT_DIR


def run_disposition(output_dir_name: str, action: str, upi: str) -> dict:
    """
    Generate a transaction text file and process it to capture screenshots.

    Args:
        output_dir_name: The timestamped folder name containing generated test files.
        action: The action to perform on the transaction (e.g., 'release', 'reject').
        upi: The UPI to use for the transaction.

    Returns:
        A dict with the JSON result from process_transaction.
    """
    # Build paths
    txt_folder = os.path.join(OUTPUT_DIR, output_dir_name)
    os.makedirs(txt_folder, exist_ok=True)
    # Sanitize UPI and action to safe filename components
    safe_upi = re.sub(r"[^\w]", "", upi)
    safe_action = re.sub(r"[^\w\-]", "", action)
    txt_name = f"{safe_upi}-{safe_action}.txt"
    txt_path = os.path.join(txt_folder, txt_name)

    # Normalize action to match expected casing
    action_lower = action.lower()
    action_map = {
        'stp-release': 'STP-Release',
        'release': 'Release',
        'block': 'Block',
        'reject': 'Reject'
    }
    norm_action = action_map.get(action_lower)
    if not norm_action:
        raise ValueError(f"Unknown action '{action}'")
    # Write transaction instruction lines: transaction, action, and comment
    transaction = upi
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"{transaction}\n{norm_action}\nBEYOND")

    # Run Playwright processor
    with sync_playwright() as p:
        result_str = process_transaction(p, txt_path)

    try:
        result = json.loads(result_str)
    except Exception:
        # Fallback if already a dict
        result = result_str
    # Attach screenshot path for PDF generation
    date_folder = datetime.now().strftime("%Y-%m-%d")
    screenshot_folder = os.path.join(OUTPUT_DIR, date_folder, upi)
    result["screenshot_path"] = screenshot_folder
    return result
