"""BPM Page object model and helpers for UI automation flows.

This module defines the `Options` enumeration and the `BPMPage` page-object class
used by Playwright scripts to automate State Street’s BPM UI.
"""

# pylint: disable=invalid-name,line-too-long,logging-fstring-interpolation,broad-exception-raised,no-else-return,missing-module-docstring,missing-function-docstring

import logging
import time
from enum import Enum
from playwright.sync_api import expect, Page


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
        self.menu_item = page.locator("div.modal-content[role='document']")

    def safe_click(self, locator, description: str):
        if locator.is_visible():
            locator.click()
            logging.debug("Clicked on %s.", description)
        else:
            msg = f"{description} is not visible."
            logging.error(msg)
            raise Exception(msg)

    def verify_modal_visibility(self) -> None:
        try:
            if self.menu_item.is_visible():
                logging.debug("<div class='modal-content' role='document'> is visible.")
            else:
                raise Exception(
                    "<div class='modal-content' role='document'> is not visible."
                )
        except Exception as e:
            logging.error("Failed to verify modal visibility: %s", e)
            raise

    def click_tick_box(self) -> None:
        try:
            tick_box = self.page.locator("li:has-text('ORI') i.fa-square-o")
            self.safe_click(tick_box, "tick box with text 'ORI'")
        except Exception as e:
            logging.error("Failed to click on the tick box with text 'ORI': %s", e)
            raise

    def click_ori_tsf(self) -> None:
        try:
            self.safe_click(
                self.page.locator("div i:has-text('ORI-TSF')"),
                "element with text 'ORI-TSF'",
            )
        except Exception as e:
            logging.error("Failed to click on the element with text 'ORI-TSF': %s", e)
            raise

    def check_options(self, options: list[Options]) -> None:

        try:
            logging.debug("Checking options: %s", options)
            for option in options:
                option_locator = self.page.locator(
                    f"li span.inf-name:has-text('{option.value}') i.fa-square-o"
                )
                self.safe_click(option_locator, f"option '{option.value}'")
                time.sleep(1)

                # Verify the option is now checked by looking for the selected icon (fa-check-square-o)
                selected_locator = self.page.locator(
                    f"li span.inf-name:has-text('{option.value}') i.fa-check-square-o"
                )
                if selected_locator.is_visible():
                    logging.debug("Verified option '%s' is selected.", option.value)
                else:
                    logging.warning(
                        "Warning: After clicking, option '%s' does NOT appear selected.",
                        option.value,
                    )
        except Exception as e:
            logging.error("Failed to check specified options in the list: %s", e)
            raise

    def click_submit_button(self) -> None:
        """Click the form's primary Submit button."""
        try:
            self.page.click("button.btn.btn-primary")
            logging.debug("Clicked on the Submit button.")
        except Exception as e:
            logging.error("Failed to click on the Submit button: %s", e)
            raise

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
    def search_results(self, number_to_look_for: str, return_all: bool = True):
        """Wait for results grid and return results.

        By default returns a tuple of (4th_column, last_column).
        If return_all=True, returns a list[str] with all column values for the row.

        Returns ("NotFound", "NotFound") or [] on error/missing.
        """
        try:
            # self.select_all_from_dropdown()  # optional dropdown action
            # self.page.wait_for_timeout(2000)
            self.wait_for_page_to_load()

            if return_all:
                columns = self.get_row_columns_for_number(number_to_look_for)
                logging.debug("All column values: %s", columns)
                return columns
            else:
                fourth_val, last_val = self.look_for_number(number_to_look_for)
                logging.debug("4th Column Value: %s", fourth_val)
                logging.debug("Last Column Value: %s", last_val)
                return fourth_val, last_val
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error in search_results: %s", e)
            return [] if return_all else ("NotFound", "NotFound")

    def perform_advanced_search(self, transaction_id: str) -> tuple:
        """Navigate to Search tab, fill reference field, submit, then fetch results."""
        logging.debug(
            "Navigating to Search tab and performing advanced search for transaction ID: %s",
            transaction_id,
        )
        self.click_search_tab()
        # self.page.wait_for_timeout(1000)
        # Log all advanced-search labels to help find the correct REFERENCE input
        # self.debug_list_advanced_fields()
        # self.page.wait_for_timeout(1000)
        self.fill_transaction_id(transaction_id)
        self.click_submit_button()
        # self.page.wait_for_timeout(2000)
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
        try:
            logging.debug("Navigating to Search.")
            search_tab = self.page.locator("li.nav-item.nav-link a[href='#search']")
            self.safe_click(search_tab, "Search tab")
        except Exception as e:
            logging.error("Failed to click on the Search tab: %s", e)
            raise

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
        try:
            self.page.wait_for_load_state("networkidle")
            logging.debug("Page has finished loading.")
        except Exception as e:
            logging.error("Failed to wait for the page to finish loading: %s", e)
            raise

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

    def get_row_columns_for_number(self, number: str) -> list[str]:
        """Return all column values for the first row containing the given number.

        Raises on selector failures; returns list[str].
        """
        try:
            number_element = self.page.locator(f"div.tcell[title='{number}']")
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
