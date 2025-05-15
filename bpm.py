import os
import sys
import logging

# Add current directory to path to find local modules
sys.path.append(os.path.dirname(os.path.abspath(".")))

# Third-party imports
from playwright.sync_api import Page, expect, sync_playwright
from Bpm_Page import BPMPage, Options

# --- Config ---

INCOMING_DIR = "input"
OUTPUT_DIR = "output"
LOG_FILE = "logs/transactions.log"
TEST_URL = "https://bpm.com/mtexrt/"
USERNAME = "user"
PASSWORD = "pass"


# --- Logging Setup ---
def setup_logging() -> None:
    """Set up logging configuration with file and console handlers."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] :: %(name)s :: %(funcName)s :: %(message)s",
        datefmt="%X",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


# --- Modular Actions ---
def perform_login_and_setup(bpm_page: BPMPage):
    bpm_page.login(TEST_URL, USERNAME, PASSWORD)
    bpm_page.verify_modal_visibility()
    bpm_page.click_tick_box()
    bpm_page.click_ori_tsf()


def select_options_and_submit(bpm_page: BPMPage, page: Page, options_to_check):
    bpm_page.check_options(options_to_check)
    bpm_page.click_submit_button()
    page.wait_for_timeout(2000)  # Consider replacing with wait_for_selector if possible
    bpm_page.click_first_row_total_column()
    page.wait_for_timeout(2000)


def handle_dropdown_and_search(bpm_page: BPMPage, page: Page, number_to_look_for: str):
    bpm_page.select_all_from_dropdown()
    page.wait_for_timeout(2000)
    bpm_page.wait_for_page_to_load()

    fourth_column_value, last_column_value = bpm_page.look_for_number(
        number_to_look_for
    )
    logging.info(f"4th Column Value: {fourth_column_value}")
    logging.info(f"Last Column Value: {last_column_value}")


# --- Main Script ---
def map_transaction_type_to_option(transaction_type_str):
    try:
        return [Options[transaction_type_str]]
    except KeyError:
        logging.warning(f"Unknown transaction type: {transaction_type_str}")
        return []


def main(transaction_type_str=None):
    setup_logging()
    if not transaction_type_str:
        logging.info("Transaction type is 'Not defined'; skipping BPM search.")
        return {
            "status": "transaction_type_not_defined",
            "message": "Transaction type was not defined, BPM search was skipped.",
        }
    number_to_look_for = "202505140000031"
    options_to_check = map_transaction_type_to_option(transaction_type_str)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.new_context()
        page = context.new_page()
        bpm_page = BPMPage(page)

        try:
            perform_login_and_setup(bpm_page)
            select_options_and_submit(bpm_page, page, options_to_check)
            handle_dropdown_and_search(bpm_page, page, number_to_look_for)

        except Exception as e:
            logging.error("An error occurred: %s", e)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
