import logging
import sys
from pathlib import Path
from typing import List, Optional
import argparse

"""Ensure repo root is importable when running this file directly.
This allows `import utils...` to resolve even if CWD is bpm/.
"""
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright

from utils.utils import login_to
from bpm.bpm_page import BPMPage, Options


def bpm_search(
    url: str,
    username: str,
    password: str,
    transaction_id: str,
    selected_options: Optional[List[Options]] = None,
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

            # Optionally select market/transaction-type filters before search
            if selected_options:
                bpm.check_options_and_submit(selected_options)

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
    parser.add_argument(
        "--options",
        help="Comma-separated list of BPM options to select (by value, e.g., 'CBPR-MX,SEPA-Classic').",
    )
    parser.add_argument(
        "--list-options",
        action="store_true",
        help="List available BPM Options and exit",
    )
    args = parser.parse_args()

    if args.list_options:
        print("Available BPM Options (name = value):")
        for opt in Options:
            print(f"- {opt.name} = {opt.value}")
        return 0

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    # Parse selected options if provided
    selected: Optional[List[Options]] = None
    if args.options:
        raw_values = [s.strip() for s in args.options.split(",") if s.strip()]
        # Match by enum value (shown in UI)
        valid_map = {opt.value: opt for opt in Options}
        selected = []
        for val in raw_values:
            if val in valid_map:
                selected.append(valid_map[val])
            else:
                logging.warning(
                    "Unknown option '%s' ignored. Use --list-options to see valid values.",
                    val,
                )

    columns = bpm_search(
        args.url,
        args.username,
        args.password,
        args.transaction,
        selected_options=selected,
    )
    if not columns:
        print("[]")
        return 1

    # Print as a simple JSON-like list for easy consumption
    print(columns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
