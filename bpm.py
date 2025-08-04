"""BPM UI-automation entry point for MURDOCK tooling."""

import os
import sys
import logging

# Third-party imports
from playwright.sync_api import sync_playwright
from Bpm_Page import BPMPage, Options

# Add project root so local modules resolve even when executed from elsewhere
sys.path.append(
    os.path.dirname(os.path.abspath("."))
)  # pylint: disable=wrong-import-position

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
    """Clear browser cookies and perform the initial BPM login/setup steps."""
    logging.info("Starting login and setup flow.")
    # Ensure a clean session by clearing any existing cookies before login
    bpm_page.page.context.clear_cookies()

    bpm_page.login(TEST_URL, USERNAME, PASSWORD)
    bpm_page.verify_modal_visibility()
    bpm_page.click_tick_box()
    bpm_page.click_ori_tsf()
    logging.info("Login and initial setup completed.")


def map_transaction_type_to_option(transaction_type_str: str):
    """Map a transaction type string (from UI) to the corresponding Options enum.

    The front-end sends the HTML option `value` – this may match either the
    Enum *name* (e.g. ``APS_MT``) **or** the Enum *value* (e.g. ``APS-MT``).
    This helper normalises the input and returns a list with the matching
    ``Options`` entry so ``check_options`` can click the right item.
    """
    if not transaction_type_str:
        logging.warning("Transaction type string is empty – no options to map.")
        return []

    # 1. Try direct Enum name match (case-sensitive)
    if transaction_type_str in Options.__members__:
        return [Options[transaction_type_str]]

    # 2. Fallback: compare against Enum values (case-insensitive)
    for opt in Options:
        if opt.value.lower() == transaction_type_str.lower():
            return [opt]

    logging.warning(
        "Unknown transaction type received from UI: %s", transaction_type_str
    )
    return []


def main(transaction_type_str=None):
    """Entry point callable; launches Playwright and drives the BPM UI.

    Args:
        transaction_type_str: Market/transaction type supplied via CLI or API.
    Returns:
        dict: status information if transaction type missing, otherwise None.
    """
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
        # browser = p.chromium.connect_over_cdp("http://localhost:9222")
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        bpm_page = BPMPage(page)

        try:
            perform_login_and_setup(bpm_page)
            bpm_page.check_options_and_submit(options_to_check)
            bpm_page.perform_advanced_search(number_to_look_for)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("An error occurred: %s", e)
        finally:
            context.close()
            # browser.close()

    # Successful completion path
    return {"status": "ok"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run BPM automation for a given market/transaction type."
    )
    parser.add_argument(
        "transaction_type",
        nargs="?",
        default=None,
        help="Market/transaction type (e.g. APS_MT or 'APS-MT').",
    )
    cli_args = parser.parse_args()

    # Initialise logging before emitting any log messages
    setup_logging()
    logging.info("CLI transaction type argument: %s", cli_args.transaction_type)
    main(cli_args.transaction_type)
