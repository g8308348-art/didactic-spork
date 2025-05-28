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
DROPDOWN_WORKFLOW = ("rc_select_1", "ORI - TSF DEH ISO")

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
def main(test_data_dir_override=None):
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

            # Determine which test data directory to use
            if test_data_dir_override:
                test_data_dir = test_data_dir_override
            else:
                # Upload files: determine test_data directory
                PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
                # Allow overriding via env or default to project-root/test_data or C:/test_data
                env_dir = os.environ.get("TEST_DATA_DIR")
                if env_dir and os.path.isdir(env_dir):
                    test_data_dir = env_dir
                elif os.path.isdir("C:/test_data"):
                    test_data_dir = "C:/test_data"
                else:
                    test_data_dir = os.path.join(PROJECT_ROOT, "test_data")
                logging.info(f"Looking for files in test_data directory: {test_data_dir}")
                if not os.path.isdir(test_data_dir):
                    raise FileNotFoundError(
                        f"Test data directory not found: {test_data_dir}"
                    )
            # Choose the most recent timestamped subfolder under test_data_dir
            subdirs = [d for d in os.listdir(test_data_dir) if os.path.isdir(os.path.join(test_data_dir, d))]
            if not subdirs:
                raise FileNotFoundError(f"No subdirectories in test_data: {test_data_dir}")
            latest = sorted(subdirs)[-1]
            target_dir = os.path.join(test_data_dir, latest)
            logging.info(f"Uploading files from subfolder: {target_dir}")
            # Collect files in that subfolder
            file_paths = []
            for root, dirs, files in os.walk(target_dir):
                for f in files:
                    file_paths.append(os.path.join(root, f))
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
