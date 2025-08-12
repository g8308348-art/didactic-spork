"""firco page handler"""

import sys
import os
import logging
from playwright.sync_api import sync_playwright

# Ensure parent directory is on path so we can import project-level modules like cyber_guard
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from cyber_guard import retrieve_CONTRASENA
from firco_page import FircoPage


USERNAME = "506"
PASSWORD = retrieve_CONTRASENA(USERNAME)
MANAGER_USERNAME = "507"
MANAGER_PASSWORD = retrieve_CONTRASENA(MANAGER_USERNAME)
TEST_URL = "https://example.com"


# --- Logging Setup ---
def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log"),
        ],
    )


def run_firco_flow():
    """basic test flow"""
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    for transaction in [
        "202508052025",
        "202508052025_202508052025",
        "2024100700000195",
        "2025071600000026",  # FILTER
        "20240545677555678",  # cu_filter
    ]:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome", headless=True
            )  # Change to True for headless mode
            context = browser.new_context()
            page = context.new_page()

            firco = FircoPage(page)

            # 1. Login
            firco.login_to_firco(TEST_URL, USERNAME, PASSWORD)

            # 2. Go to Live Messages root
            firco.go_to_live_messages_root()

            firco.clear_filtered_column()
            firco.data_filters(transaction)

            firco.verify_first_row(
                transaction, firco.validate_search_table_results(), "STP-Release", "asd"
            )

            context.close()
            # I can not close the browser
            # browser.close()


if __name__ == "__main__":
    run_firco_flow()
