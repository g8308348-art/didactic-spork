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

            # Determine target directory for upload
            if test_data_dir_override:
                target_dir = test_data_dir_override
            else:
                # Base test data dir: env override, C:/test_data, or project/test_data
                PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
                env_dir = os.environ.get("TEST_DATA_DIR")
                if env_dir and os.path.isdir(env_dir):
                    base_dir = env_dir
                elif os.path.isdir("C:/test_data"):
                    base_dir = "C:/test_data"
                else:
                    base_dir = os.path.join(PROJECT_ROOT, "test_data")
                if not os.path.isdir(base_dir):
                    raise FileNotFoundError(
                        f"Test data directory not found: {base_dir}"
                    )
                # Pick the latest timestamped subfolder
                subdirs = [
                    d
                    for d in os.listdir(base_dir)
                    if os.path.isdir(os.path.join(base_dir, d))
                ]
                if not subdirs:
                    raise FileNotFoundError(
                        f"No subdirectories in test_data: {base_dir}"
                    )
                latest = sorted(subdirs)[-1]
                target_dir = os.path.join(base_dir, latest)
            logging.info(f"Uploading files from: {target_dir}")
            # Collect files in target directory
            file_paths = [
                os.path.join(r, f) for r, _, files in os.walk(target_dir) for f in files
            ]
            logging.info(f"Files to upload to MTex: {file_paths}")
            mtex_page.upload_files_and_click_button(
                'input[name="file"]', file_paths, "button.ant-btn-primary"
            )
            # Find element and center/scroll into view before screenshot
            el = page.locator('span.file-name[title="screening_response_release_xml"]')
            el.scroll_into_view_if_needed()
            # Take a full-page screenshot after scrolling element into view, saving to target_dir
            screenshot_path = os.path.join(target_dir, "mtexops.png")
            page.screenshot(path=screenshot_path, full_page=True)
            logging.info(f"MTEx screenshot saved to: {screenshot_path}")

        except Exception as e:
            logging.exception("Unhandled exception occurred")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
