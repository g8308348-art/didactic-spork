import os
import logging
import time
import sys
from playwright.sync_api import Page, expect, sync_playwright
from Mtex_Page import MtexPage

# --- Config ---
INCOMING_DIR = "input"
OUTPUT_DIR = "output"
LOG_FILE = "transactions.log"
TEST_URL = "https://cloud-ua1.com/mtexops/"
USERNAME = "e72128"
PASSWORD = "123!"

# Dropdown selectors and values
DROPDOWN_BU = ("rc_select_0", "UAT")
DROPDOWN_WORKFLOW = ("rc_select_1", "ORI - TSF RTPS SRCBYP Taiwan")

TRANSACTION_NOT_FOUND_STATUS = "transaction_not_found_in_any_tab"


# --- Logging Setup ---
def setup_logging() -> None:
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(process)03d] :: %(levelname)s :: %(name)s :: %(funcName)s :: %(message)s",
        datefmt="%X",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


# --- Main Script ---
def main():
    setup_logging()

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.new_context()
            page = context.new_page()
            mtex_page = MtexPage(page)

            # Login
            mtex_page.login(TEST_URL, USERNAME, PASSWORD)

            # Select dropdown options
            logging.info("Selecting dropdowns...")
            mtex_page.select_dropdown_option(*DROPDOWN_BU)
            mtex_page.select_dropdown_option(*DROPDOWN_WORKFLOW)

            # Wait (if needed)
            page.wait_for_timeout(500)

            # Upload files: gather all files under test_data directory
            import glob
            PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
            test_data_dir = os.path.join(PROJECT_ROOT, 'test_data')
            # Recursively collect files in test_data/**
            file_paths = [
                os.path.join(root, f)
                for root, dirs, files in os.walk(test_data_dir)
                for f in files
            ]
            logging.info(f"Files to upload to MTex: {file_paths}")
            mtex_page.upload_files_and_click_button(
                'input[name="file"]', file_paths, "button.ant-btn-primary"
            )

        except Exception as e:
            logging.exception("Unhandled exception occurred")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
