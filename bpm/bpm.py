import logging
import sys
from typing import List
import argparse

from playwright.sync_api import sync_playwright

from utils import login_to
from bpm.bpm_page import BPMPage


def bpm_search(
    url: str, username: str, password: str, transaction_id: str
) -> List[str]:
    """Open BPM, log in, perform search, and return all column values for the row.

    Returns an empty list on failure.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            if not login_to(page, url, username, password):
                logging.error("Login failed, aborting BPM search.")
                return []

            bpm = BPMPage(page)
            bpm.click_search_tab()
            page.wait_for_timeout(1000)
            bpm.fill_transaction_id(transaction_id)
            bpm.click_submit_button()
            page.wait_for_timeout(2000)

            # Ask for all columns from the results row
            columns = bpm.search_results(transaction_id, return_all=True)
            logging.info("Search results (all columns): %s", columns)
            return columns if isinstance(columns, list) else []
        finally:
            try:
                context.close()
            except Exception:  # noqa: BLE001
                pass
            try:
                browser.close()
            except Exception:  # noqa: BLE001
                pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a BPM search and print all columns for a transaction."
    )
    parser.add_argument("--url", required=True, help="BPM URL (login page)")
    parser.add_argument("--username", required=True, help="Login username")
    parser.add_argument("--password", required=True, help="Login password")
    parser.add_argument(
        "--transaction", required=True, help="Transaction/reference ID to search for"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    columns = bpm_search(args.url, args.username, args.password, args.transaction)
    if not columns:
        print("[]")
        return 1

    # Print as a simple JSON-like list for easy consumption
    print(columns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
