"""Simple, stateless helper functions for BPM Playwright interactions.

These are thin wrappers around Playwright operations, extracted from
`BPMPage` to keep the page-object lean and enable reuse.
"""

# pylint: disable=invalid-name,line-too-long,logging-fstring-interpolation,broad-exception-raised,missing-module-docstring,missing-function-docstring

import logging
import time
from enum import Enum


def safe_click(page, locator, description: str):
    if locator.is_visible():
        locator.click()
        logging.debug("Clicked on %s.", description)
    else:
        msg = f"{description} is not visible."
        logging.error(msg)
        raise Exception(msg)


def verify_modal_visibility(page) -> None:
    try:
        menu_item = page.locator("div.modal-content[role='document']")
        if menu_item.is_visible():
            logging.debug("<div class='modal-content' role='document'> is visible.")
        else:
            raise Exception(
                "<div class='modal-content' role='document'> is not visible."
            )
    except Exception as e:
        logging.error("Failed to verify modal visibility: %s", e)
        raise


def click_tick_box(page) -> None:
    try:
        tick_box = page.locator("li:has-text('ORI') i.fa-square-o")
        safe_click(page, tick_box, "tick box with text 'ORI'")
    except Exception as e:
        logging.error("Failed to click on the tick box with text 'ORI': %s", e)
        raise


def click_ori_tsf(page) -> None:
    try:
        elem = page.locator("div i:has-text('ORI-TSF')")
        safe_click(page, elem, "element with text 'ORI-TSF'")
    except Exception as e:
        logging.error("Failed to click on the element with text 'ORI-TSF': %s", e)
        raise


def _opt_value(opt) -> str:
    # Supports Enum with .value or raw strings
    return getattr(opt, "value", opt)


def check_options(page, options: list) -> None:
    try:
        logging.debug("Checking options: %s", options)
        for option in options:
            val = _opt_value(option)
            option_locator = page.locator(
                f"li span.inf-name:has-text('{val}') i.fa-square-o"
            )
            safe_click(page, option_locator, f"option '{val}'")
            time.sleep(1)

            # Verify the option is now checked by looking for the selected icon (fa-check-square-o)
            selected_locator = page.locator(
                f"li span.inf-name:has-text('{val}') i.fa-check-square-o"
            )
            if selected_locator.is_visible():
                logging.debug("Verified option '%s' is selected.", val)
            else:
                logging.warning(
                    "Warning: After clicking, option '%s' does NOT appear selected.",
                    val,
                )
    except Exception as e:
        logging.error("Failed to check specified options in the list: %s", e)
        raise


def click_submit_button(page) -> None:
    try:
        page.click("button.btn.btn-primary")
        logging.debug("Clicked on the Submit button.")
    except Exception as e:
        logging.error("Failed to click on the Submit button: %s", e)
        raise


def click_search_tab(page) -> None:
    """Navigate to the Search tab in BPM."""
    try:
        logging.debug("Navigating to Search.")
        search_tab = page.locator("li.nav-item.nav-link a[href='#search']")
        safe_click(page, search_tab, "Search tab")
    except Exception as e:
        logging.error("Failed to click on the Search tab: %s", e)
        raise


def wait_for_page_to_load(page) -> None:
    try:
        page.wait_for_load_state("networkidle")
        logging.debug("Page has finished loading.")
    except Exception as e:
        logging.error("Failed to wait for the page to finish loading: %s", e)
        raise


def get_row_columns_for_number(page, number: str) -> list[str]:
    """Return all column values for the first row containing the given number."""
    try:
        number_element = page.locator(f"div.tcell[title='{number}']")
        if number_element.count() == 0:
            raise Exception(f"Number {number} is not visible.")

        first_element = number_element.first
        first_element.evaluate(
            "element => element.scrollIntoView({block: 'center', inline: 'center'})"
        )
        parent_row = first_element.locator(
            "xpath=ancestor::div[contains(@class, 'trow')]"
        )
        # Collect all cell texts in the row
        columns = parent_row.locator("div.tcell").all_inner_texts()
        return [c.strip() for c in columns]
    except Exception as e:

        logging.error("Failed to get all columns for number %s: %s", number, e)
        return []


def map_transaction_type_to_option(tx_type: str, Options: Enum):
    """Map incoming transaction_type string to BPM Options enum.

    Accepts either:
    - the display value (e.g., 'EnterpriseISO', 'CBPR-MX'), or
    - the enum name (e.g., 'ENTERPRISE_ISO', 'CBPR_MX').
    Returns the matching Options member or None if not found.
    """
    try:
        if not tx_type:
            return None
        s = (tx_type or "").strip()
        # 1) Exact match on display value
        for o in Options:
            if o.value == s:
                return o
        # 2) Match on enum name (case-insensitive, allow hyphen/space vs underscore)
        normalized = s.upper().replace("-", "_").replace(" ", "_")
        try:
            return Options[normalized]
        except KeyError:
            return None
    except Exception:
        return None
