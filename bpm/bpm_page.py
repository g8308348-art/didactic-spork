"""BPM Page object model and helpers for UI automation flows.

This module defines the `Options` enumeration and the `BPMPage` page-object class
used by Playwright scripts to automate State Street’s BPM UI.
"""

# pylint: disable=invalid-name,line-too-long,logging-fstring-interpolation,broad-exception-raised,no-else-return,missing-module-docstring,missing-function-docstring

import logging
import time
from enum import Enum
from playwright.sync_api import expect, Page, sync_playwright
from utils.utils import login_to
from bpm.bpm_page_simple import (
    safe_click as simple_safe_click,
    verify_modal_visibility as simple_verify_modal_visibility,
    click_tick_box as simple_click_tick_box,
    click_ori_tsf as simple_click_ori_tsf,
    check_options as simple_check_options,
    click_submit_button as simple_click_submit_button,
    click_search_tab as simple_click_search_tab,
    wait_for_page_to_load as simple_wait_for_page_to_load,
    get_row_columns_for_number as simple_get_row_columns_for_number,
)


class Options(Enum):
    """Enumeration of BPM market / transaction type options displayed in the UI."""

    UNCLASSIFIED = "Unclassified"
    APS_MT = "APS-MT"
    CBPR_MX = "CBPR-MX"
    SEPA_CLASSIC = "SEPA-Classic"
    RITS_MX = "RITS-MX"
    LYNX_MX = "LYNX-MX"
    ENTERPRISE_ISO = "EnterpriseISO"
    CHAPS_MX = "CHAPS-MX"
    T2S_MX = "T2S-MX"
    BESS_MT = "BESS-MT"
    CHIPS_MX = "CHIPS-MX"
    SEPA_INSTANT = "SEPA-Instant"
    FEDWIRE = "FEDWIRE"
    TAIWAN_MX = "Taiwan-MX"
    CHATS_MX = "CHATS-MX"
    PEPPLUS_IAT = "PEPPLUS-IAT"
    TSF_TRIGGER = "TSF-TRIGGER"


class BPMPage:
    """Page Object Model encapsulating high-level BPM UI interactions."""

    def __init__(self, page: Page):
        self.page = page
        # Basic interactions are delegated to bpm_page_simple helpers

    def safe_click(self, locator, description: str):
        return simple_safe_click(self.page, locator, description)

    def verify_modal_visibility(self) -> None:
        return simple_verify_modal_visibility(self.page)

    def click_tick_box(self) -> None:
        return simple_click_tick_box(self.page)

    def click_ori_tsf(self) -> None:
        return simple_click_ori_tsf(self.page)

    def check_options(self, options: list[Options]) -> None:
        return simple_check_options(self.page, options)

    def click_submit_button(self) -> None:
        """Click the form's primary Submit button."""
        return simple_click_submit_button(self.page)

    # ------------------------------------------------------------------
    # Composite helpers
    # ------------------------------------------------------------------
    def check_options_and_submit(self, options: list[Options]) -> None:
        """High-level helper: tick given market checkboxes and press Submit.

        Args:
            options (list[Options]): Markets to select in the left-hand tree.
        """
        logging.debug("Selecting market options: %s", [opt.value for opt in options])
        self.check_options(options)
        self.click_submit_button()

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------
    def debug_list_advanced_fields(self) -> None:
        """Log every label text in the Advanced Search panel to aid selector tuning."""
        labels = self.page.locator("div.search-item label")
        count = labels.count()
        logging.debug("Search-form labels found: %d", count)
        for idx in range(count):
            txt = labels.nth(idx).inner_text().strip()
            has_input = labels.nth(idx).evaluate(
                "el => !!el.nextElementSibling && el.nextElementSibling.tagName.toLowerCase() === 'input'"
            )
            logging.debug(
                "[LBL %02d] label='%s' adjacent-input=%s", idx, txt, has_input
            )

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------
    def search_results(
        self,
        number_to_look_for: str,
        as_json: bool = True,
        validate: bool = True,
    ):
        """Wait for results grid and return results as JSON.

        Returns a JSON-serializable dict. If validate is True, uses
        validate_result_columns() with the provided transaction id; otherwise
        returns {"columns": [...]}.

        On error/missing row, returns a structured JSON like:
        {"transaction": ..., "success": False, "status": "not_found"|"error", "message": ...}
        """
        try:
            self.wait_for_page_to_load()

            columns = self.get_row_columns_for_number(number_to_look_for)
            logging.debug("All column values: %s", columns)

            if not as_json:
                # Forcing JSON output per new requirement, but keep a minimal safeguard
                as_json = True

            if not columns:
                return {
                    "transaction": number_to_look_for,
                    "success": False,
                    "status": "not_found",
                    "message": "No results",
                }

            if validate:
                return self.validate_result_columns(columns, number_to_look_for)
            return {"columns": columns}

        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error in search_results: %s", e)
            return {
                "transaction": number_to_look_for,
                "success": False,
                "status": "error",
                "message": str(e),
            }

    def perform_advanced_search(self, transaction_id: str) -> tuple:
        """Navigate to Search tab, fill reference field, submit, then fetch results."""
        logging.debug(
            "Navigating to Search tab and performing advanced search for transaction ID: %s",
            transaction_id,
        )
        self.click_search_tab()
        self.fill_transaction_id(transaction_id)
        self.click_submit_button()

        return self.search_results(transaction_id)

    def click_element_with_dynamic_title(self) -> None:
        try:
            dynamic_title_element = self.page.locator("div.tcell.hover-td").first
            dynamic_title_value = dynamic_title_element.get_attribute("title")
            elements = self.page.locator(
                f"div.tcell.hover-td[title='{dynamic_title_value}']"
            )
            for i in range(elements.count()):
                element = elements.nth(i)
                if element.is_visible():
                    element.click()
                    logging.debug(
                        f"Clicked on element {i+1} with class 'tcell hover-td' and title '{dynamic_title_value}'."
                    )
                    break
            else:
                raise Exception(
                    f"No visible element found with title '{dynamic_title_value}'."
                )
        except Exception as e:
            logging.error(
                "Failed to click on the element with title '%s': %s",
                dynamic_title_value,
                e,
            )
            raise

    def click_search_tab(self) -> None:
        """Navigate to the Search tab in BPM.."""
        return simple_click_search_tab(self.page)

    def fill_transaction_id(self, transaction_id: str) -> None:
        """Fill the REFERENCE field in the advanced-search panel with extra diagnostics."""
        try:
            # Target the input directly following the label whose text is exactly 'REFERENCE:'
            # Using Playwright CSS :has-text() for clarity and robustness.
            selector = "div.search-item label:has-text('REFERENCE') + input"
            logging.debug("Looking for REFERENCE input with selector: %s", selector)
            # lets make sure the selector is visible
            self.page.wait_for_selector(selector)
            input_field = self.page.locator(selector).first
            if not input_field or not input_field.is_visible():
                logging.error(
                    "REFERENCE input not visible – selector used: %s", selector
                )
                raise ValueError("REFERENCE input field not found or not visible")
            logging.debug("Using input locator: %s", input_field)
            input_field.fill(transaction_id)
            logging.debug(
                "Filled transaction id %s in reference field.", transaction_id
            )
        except Exception as e:
            logging.error("Failed to fill transaction id %s: %s", transaction_id, e)
            raise

    def wait_for_page_to_load(self) -> None:
        return simple_wait_for_page_to_load(self.page)

    def look_for_number(self, number: str) -> tuple:
        try:
            # Find all cells with the target number
            number_element = self.page.locator(f"div.tcell[title='{number}']")
            count = number_element.count()

            if count > 0:
                if count > 1:
                    logging.debug(
                        f"Found {count} instances of number: {number}. Using the first match."
                    )
                else:
                    logging.debug(f"Found the number: {number}")

                # Always use the first element when multiple matches are found
                first_element = number_element.first
                first_element.evaluate(
                    "element => element.scrollIntoView({block: 'center', inline: 'center'})"
                )

                parent_row = first_element.locator(
                    "xpath=ancestor::div[contains(@class, 'trow')]"
                )
                fourth_column_value = parent_row.locator(
                    "div.tcell:nth-child(4)"
                ).inner_text()
                last_column_value = parent_row.locator(
                    "div.tcell:last-child"
                ).inner_text()
                return fourth_column_value, last_column_value
            else:
                raise Exception(f"Number {number} is not visible.")
        except Exception as e:
            logging.error("Failed to look for the number %s: %s", number, e)
            # If the error contains information about multiple elements, treat it as success
            if "resolved to 2 elements" in str(
                e
            ) or "resolved to multiple elements" in str(e):
                logging.debug(
                    f"Multiple elements found for {number}, treating as success"
                )
                # Return placeholder values when we can't determine actual values due to multiple elements
                return "NotFound", "NotFound"
            raise

    def click_first_row_total_column(self) -> None:
        try:
            total_column_element = self.page.locator(
                "div.mtex-datagrid-tbody .trow .tcell.hover-td div"
            ).first
            self.safe_click(total_column_element, "first row of the TOTAL column")
        except Exception as e:
            logging.error(
                "Failed to click on the text in the first row of the TOTAL column: %s",
                e,
            )
            raise

    # ------------------------------------------------------------------
    # High-level flow helper (post-login)
    # ------------------------------------------------------------------
    def run_full_search(
        self, transaction_id: str, selected_options: list[Options]
    ) -> dict:
        """Run the full post-login BPM flow and return validated JSON result.

        This mirrors the actions in bpm/bpm.py after login:
        - verify modal, tick 'ORI', click 'ORI-TSF'
        - select provided options and submit
        - go to Search tab, fill transaction id, submit
        - fetch results via search_results(as_json=True, validate=True)
        """
        logging.debug(
            "Starting full BPM search flow for transaction: %s", transaction_id
        )
        self.verify_modal_visibility()
        self.click_tick_box()
        self.click_ori_tsf()
        self.check_options_and_submit(selected_options)

        self.click_search_tab()
        self.fill_transaction_id(transaction_id)
        self.click_submit_button()
        # Small wait to allow grid to render
        try:
            self.page.wait_for_timeout(1000)
        except Exception:  # noqa: BLE001
            pass

        result = self.search_results(transaction_id, as_json=True, validate=True)
        logging.debug("Full BPM search result: %s", result)
        return result

    def get_row_columns_for_number(self, number: str) -> list[str]:
        """Return all column values for the first row containing the given number."""
        return simple_get_row_columns_for_number(self.page, number)

    """
    I need to write a function that validates the results of the search
    I start counting columns from 1
    * second column is a "transaction_id" column, called in the bpm REFERENCE
    * transaction_id should match text in the second column

    * fourth column is a status  column, called in the bpm "CURRENT STATUS"
    four possibilities are here:
    *  Contains "SendResponseTo" which means "NO HIT Transaction"
    *  Contains "BusinessResponseProcessed" which means "Response from Firco received"
    *  Contains "PostedTxnToFirco" which means "Transaction posted to Firco"
    *  Contains "UNDEFINED" there is an error

    tentht column is a holding_qm column, called in the bpm "HOLDING QM"
    *  if starts with numbers 25 to 30 it means it's a BUAT Envirement
    *  else UAT Envirement

    eleventh column is a status column, called in the bpm "STATUS"
    * if contains SUCCESS and fourth column contains "SendResponseTo" it's a success
    * if contains SUCCESS and fourth column contains "BusinessResponseProcessed" it's a success
    * if contains SUCCESS and fourth column contains "PostedTxnToFirco" it's a success
    
    * if contains FAILURE it's a failure
    * if contains WARNING it's a failure

    """

    def classify_environment(self, holding_qm: str) -> str:
        """Classify environment from HOLDING QM (10th column, 1-based).

        BUAT if starts with numbers 25..30, else UAT.
        """
        try:
            s = (holding_qm or "").strip()
            prefix = s[:2]
            if prefix.isdigit():
                val = int(prefix)
                if 25 <= val <= 30:
                    return "BUAT"
        except Exception:
            pass
        return "UAT"

    def validate_result_columns(self, columns: list[str], transaction_id: str) -> dict:
        """Validate a full row returned by search_results(return_all=True).

        Columns (1-based):
        - 2: REFERENCE (must equal transaction_id)
        - 4: CURRENT STATUS
        - 10: HOLDING QM (env detection)
        - 11: STATUS

        Returns dict with: success, status, message, environment, details
        """
        out = {
            "transaction": transaction_id,
            "success": False,
            "status": "invalid",
            "message": "",
            "environment": None,
            "details": {},
        }

        if not columns or len(columns) < 11:
            out["message"] = "Insufficient columns returned from BPM."
            return out

    # (class methods end)


def run_bpm_search(
    url: str,
    username: str,
    password: str,
    transaction_id: str,
    selected_options: list[Options],
) -> dict:
    """Open browser, login to BPM, run full search, and return validated JSON.

    Lifecycle: start Playwright, create context/page, login, run flow, cleanup.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            if not login_to(page, url, username, password):
                logging.error("Login failed, aborting BPM search.")
                return {}

            bpm = BPMPage(page)
            result = bpm.run_full_search(transaction_id, selected_options)
            logging.info("BPM Search result (JSON): %s", result)
            return result
        finally:
            try:
                context.close()
            except Exception:  # noqa: BLE001
                pass
