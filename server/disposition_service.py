import os
import json
from playwright.sync_api import sync_playwright
from main_logic import process_transaction, OUTPUT_DIR


def run_disposition(output_dir_name: str, action: str) -> dict:
    """
    Generate a transaction text file and process it to capture screenshots.

    Args:
        output_dir_name: The timestamped folder name containing generated test files.
        action: The action to perform on the transaction (e.g., 'release', 'reject').

    Returns:
        A dict with the JSON result from process_transaction.
    """
    # Build paths
    txt_folder = os.path.join(OUTPUT_DIR, output_dir_name)
    os.makedirs(txt_folder, exist_ok=True)
    txt_name = f"{output_dir_name}-{action}.txt"
    txt_path = os.path.join(txt_folder, txt_name)

    # Write transaction instruction line
    transaction = output_dir_name
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"{transaction}|{action}|BEYOND")

    # Run Playwright processor
    with sync_playwright() as p:
        result_str = process_transaction(p, txt_path)

    try:
        return json.loads(result_str)
    except Exception:
        # Fallback if already a dict
        return result_str
