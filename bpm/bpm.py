"""BPM UI-automation entry point for MURDOCK tooling."""

import os
import logging

# Third-party imports
from playwright.sync_api import sync_playwright

from .bpm_page import (
    BPMPage,
    perform_login_and_setup,
    map_transaction_type_to_option,
)

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
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.new_context()
        page = context.new_page()
        bpm_page = BPMPage(page)

        try:
            perform_login_and_setup(bpm_page, TEST_URL, USERNAME, PASSWORD)
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
