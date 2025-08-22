"""Firco CLI runner, modeled after bpm/bpm.py."""

import sys
import os
import json
import time
import argparse
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from playwright.sync_api import sync_playwright

# Ensure parent directory is on path so we can import project-level modules like cyber_guard
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from firco_page import FircoPage  # noqa: E402


def _firco_run_sync(transaction: str, action: str, comment: str = "", transaction_type: str = "") -> Dict:
    """Run Firco flow using the sync Playwright API (meant for non-async threads)."""
    with sync_playwright() as p:
        # Use bundled Chromium to avoid Chrome dependency
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            firco = FircoPage(page)
            result = firco.flow_start(transaction, action, comment, transaction_type)
            logging.info("Firco result (JSON): %s", result)
            return result
        finally:
            try:
                context.close()
            except Exception:  # noqa: BLE001
                pass


def firco_run(transaction: str, action: str, comment: str = "", transaction_type: str = "") -> Dict:
    """Dispatch to sync Playwright normally, but if an asyncio loop is active, run in a thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Run the sync Playwright flow in a background thread to avoid the 'Sync API inside the asyncio loop' error.
            with ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(_firco_run_sync, transaction, action, comment, transaction_type).result()
    except RuntimeError:
        # No event loop set; fall back to direct sync call
        pass
    return _firco_run_sync(transaction, action, comment, transaction_type)


def main() -> int:
    # Measure total script duration
    t_total_start = time.perf_counter()

    # Phase 1: lightweight parser for --list-actions and --log-level
    pre = argparse.ArgumentParser(
        add_help=True,
        description="Run a Firco flow and print structured JSON result.",
    )
    pre.add_argument(
        "--list-actions",
        action="store_true",
        help="List available actions and exit",
    )
    pre.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    pre_args, _ = pre.parse_known_args()

    if pre_args.list_actions:
        print("Available actions:")
        for a in ["STP-Release", "Release", "Block", "Reject"]:
            print(f"- {a}")
        return 0

    # Phase 2: full parser
    parser = argparse.ArgumentParser(
        description="Run a Firco flow and print structured JSON result.",
    )
    parser.add_argument("--transaction", required=True, help="Transaction ID to search")
    parser.add_argument(
        "--action",
        required=True,
        help="Action to perform (use --list-actions to see valid values)",
    )
    parser.add_argument("--comment", default="", help="Comment to add")
    parser.add_argument(
        "--transaction-type",
        default="",
        help="Optional transaction type to pass through",
    )
    parser.add_argument(
        "--log-level",
        default=pre_args.log_level,
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )

    # Run
    t_run_start = time.perf_counter()
    result = firco_run(
        transaction=args.transaction,
        action=args.action,
        comment=args.comment,
        transaction_type=args.transaction_type,
    )
    t_run_end = time.perf_counter()

    logging.info(
        "Timing: firco_run=%.3fs total=%.3fs",
        (t_run_end - t_run_start),
        (time.perf_counter() - t_total_start),
    )

    if not result or not isinstance(result, dict):
        print("{}")
        return 1

    print(json.dumps(result))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
