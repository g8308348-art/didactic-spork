"""firco page POM"""

import logging
import shutil
from enum import Enum, auto
from pathlib import Path
from typing import Optional
from datetime import datetime
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from cyber_guard import retrieve_CONTRASENA
from utils.utils import (
    login_to,
    archive_screenshots,
    clear_existing_screenshots,
)

USERNAME = "506"
PASSWORD = retrieve_CONTRASENA(USERNAME)
MANAGER_USERNAME = "507"
MANAGER_PASSWORD = retrieve_CONTRASENA(MANAGER_USERNAME)
TEST_URL = "https://example.com"


class Selectors:
    """Container for page selectors to reduce attribute count in the main class."""

    def __init__(self, page: Page):
        # Navigation selectors
        self.menu_item = page.locator("li#root-menu-0")
        self.history_item = page.locator("li#root-menu-1")
        self.live_messages = page.locator("div.stick#text-element-8")
        self.live_messages_tab = page.locator("a.tab-center").filter(
            has_text="Live Messages"
        )
        self.sanctions_bypass_view_tab = page.locator("a.tab-center").filter(
            has_text="Sanctions Bypass View"
        )
        # Filtering descending date
        self.filtered_date_menu_opener = page.locator(
            "#fmf-table-column-filtered-date-col-menu-opener"
        )
        self.ascending_date = page.locator("text=Sort ascending")
        self.descending_date = page.locator("text=Sort descending")
        self.reset_filter = page.locator(".remove-sort-menu-item")

        # Table selectors
        self.table = page.locator("table")
        self.filtered_column_icon = page.locator("a.column-filtered-icon")
        self.menu_opener = page.locator("#fmf-table-column-message-id-col-menu-opener")
        self.input_field = page.locator("input.quick-filter-input")
        self.search_btn = page.locator("div.quick-filter-icon")
        self.no_data_notice = page.locator(
            "div.no-data-notice-wrapper div.no-data-notice"
        )
        self.first_odd_row_td_text = (
            page.locator("tr.odd-row").first.locator("td").first
        )
        # rows
        self.first_row_active = page.locator("tr.even-row.clickable-row")
        self.first_row_not_active = page.locator(
            "table#table-element-1 tbody tr.lowlightedRow"
        ).first
        self.padlock_icon = page.locator("div.sprite.table-icon.admin-locked-icon")
        self.unlock_overlay_titlebar = page.locator("div#overlay-titlebar")
        # Button ID contains spaces; use attribute selector to avoid CSS escaping issues
        self.close_overlay_button = page.locator("input[id='Close Overlay Button']")

        self.first_row_state_column = page.locator(
            "table#table-element-1 tbody tr.clickable-row"
        ).first.locator("td div.row-click.cell-filler")

        self.first_row_column_text = page.locator(
            "table#table-element-1 tbody tr.clickable-row"
        ).first.locator("td")

        self.comment_field = page.locator(
            "textarea.stick.ui-autocomplete-input[name='COMMENT']"
        )
        self.transaction_rows = page.locator(
            "table.hit-table.live tbody tr"
        )  # was self.table / duplicated

        self.table = page.locator("table#table-element-1")
        self.table_rows = self.table.locator("tbody tr")
        # Avoid evaluating locators during initialization; evaluate lazily later
        self.table_rows_first = self.table_rows.first

        self.data_filters = page.locator("text=Data filters...")
        self.data_filters_input = page.locator("id=text-input-element-44")
        self.data_filters_add_button = page.locator("id=Add Filter Button")
        self.data_filters_ok_button = page.locator("id=Confirm Button")

        # Navigation link to open Live Messages view (anchor has classes 'hide' and 'unload-page')
        self.live_messages_link = page.locator("li#root-menu-0 a.hide.unload-page")

        # Action buttons
        self.stp_release = page.locator("input[value='STP_Release']")
        self.confirm = page.locator("input#Confirm\\ Button")
        self.release = page.locator("input[value='Release']")
        self.reject = page.locator("input[value='Reject']")
        self.block = page.locator("input[value='Block']")
        self.logout = page.locator("#logout-button")
        self.escalate = page.locator("input[value='Esc_Sanctions']")


class SearchStatus(Enum):
    """Enum for search status."""

    NONE = auto()
    MULTIPLE = auto()
    FOUND = auto()


class TabContext(Enum):
    """Enum for tab context."""

    LIVE = auto()
    HISTORY = auto()


class FircoPage:
    """
    Wrapper class for Firco application page that handles page interactions and transaction
    processing.

    This class provides methods to interact with the Firco UI elements, search for transactions,
    and perform various actions on them such as release, block, or reject.
    """

    def __init__(self, page: Page):
        """
        Initialize the FircoPage with a Playwright page object.

        Args:
            page: The Playwright Page object to use for interactions
        """
        logging.debug("FircoPage.__init__ called")
        self.page = page
        self.selectors = Selectors(page)  # Group all selectors in a separate object

    def logout(self) -> bool:
        """
        Log out from the Firco system.

        Waits for a brief timeout to ensure all actions are complete,
        then clicks the logout button and logs the action.
        """
        self.page.wait_for_timeout(2000)
        self.selectors.logout.click()
        logging.debug("Logged out!")
        return True

    def go_to_live_messages_root(self) -> bool:
        """
        Go to the Live Messages root page.
        """
        logging.debug("Navigating to live messages link!")
        # self.sel.menu_item.click()
        self.selectors.live_messages_link.click()

        expect(self.selectors.live_messages).to_contain_text("Live Messages")

        try:
            expect(self.selectors.live_messages_tab).to_be_visible()
            expect(self.selectors.live_messages_tab).to_have_class(
                r"tab-center tab-center-selected"
            )
        except PlaywrightTimeoutError as e:
            logging.debug("Live Messages tab not active: %s", e)
            logging.debug("Clicking on Live Messages tab.")
            self.selectors.live_messages_tab.click()
            expect(self.selectors.live_messages_tab).to_have_class(
                r"tab-center tab-center-selected"
            )
        return True

    def go_to_history_root(self, transaction: str, action: str, comment: str) -> bool:
        """Go to the History root page."""
        logging.debug("Navigating to history link!")
        try:
            self.selectors.history_item.click()
            self.page.wait_for_timeout(2000)
            # Clear any existing filters and search for the transaction
            self.clear_filtered_column()
            self.data_filters(transaction)
            self.verify_first_row(
                transaction, self.validate_search_table_results(), action, comment
            )
            self.page.screenshot(path="history_root.png", full_page=True)
            return True
        except PlaywrightTimeoutError as e:
            logging.error("go_to_history_root triggered timeout.")
            logging.error("go_to_history_root error: %s", e)
            return False

    def clear_filtered_column(self) -> bool:
        """
        Clear any filters that may be applied to the transaction column.

        Checks if a filter icon is visible and clicks it if present. Verifies the action
        was successful and logs detailed feedback.
        """
        try:
            if self.selectors.filtered_column_icon.is_visible(timeout=5000):
                logging.debug("Filter icon detected. Attempting to clear filter.")
                self.selectors.filtered_column_icon.click()
                # Verify if the filter icon is still visible after clicking
                if self.selectors.filtered_column_icon.is_visible(timeout=2000):
                    logging.warning(
                        "Filter icon still visible after click. Filter may not have cleared."
                    )
                else:
                    logging.debug("Filter successfully cleared.")
            else:
                logging.debug(
                    "No filter icon detected in transaction column. No action needed."
                )
        except PlaywrightTimeoutError as e:
            logging.error("clear_filtered_column triggered timeout.")
            logging.error("clear_filtered_column error: %s", e)
        return True

    def data_filters(self, transaction: str) -> bool:
        """search for transaction number"""
        try:
            logging.debug("Applying data filters for transaction: %s", transaction)
            self.selectors.menu_opener.click()
            self.selectors.data_filters.click()
            self.page.fill("id=text-input-element-44", transaction)
            self.page.click("id=Add Filter Button")
            self.page.click("id=Confirm Button")
            self.page.screenshot(path="data_filters.png", full_page=True)
            self.page.wait_for_timeout(2000)
        except PlaywrightTimeoutError as e:
            logging.error("data_filters triggered timeout.")
            logging.error("data_filters error: %s", e)
        return True

    def detect_tab(self) -> TabContext:
        """Decide which tab we're on once, then reuse."""
        try:
            # If a 'History Messages' marker is visible quickly, treat as HISTORY.
            if self.selectors.live_messages.filter(
                has_text="History Messages"
            ).is_visible(timeout=800):
                return TabContext.HISTORY
        except PlaywrightTimeoutError:
            pass
        return TabContext.LIVE

    def validate_search_table_results(self) -> SearchStatus:
        """validate results of search"""
        logging.debug("Validating search results.")
        try:
            if self.selectors.no_data_notice.is_visible():
                logging.debug("No data found.")
                self.page.screenshot(path="no_transactions.png", full_page=True)
                return SearchStatus.NONE

            if (self.selectors.first_odd_row_td_text.text_content() or "").strip():
                logging.debug("Multiple transactions found.")
                self.sort_multiple_transactions()
                self.page.screenshot(path="multiple_transactions.png", full_page=True)
                return SearchStatus.MULTIPLE

            self.page.screenshot(path="one_transaction.png", full_page=True)
            logging.debug("One transaction found.")
            return SearchStatus.FOUND

        except PlaywrightTimeoutError as e:
            logging.error("validate_results triggered timeout.")
            logging.error("validate_results error: %s", e)
        return SearchStatus.NONE

    def verify_first_row(
        self, transaction: str, status: SearchStatus, action: str, comment: str
    ) -> bool:
        """Verify the first row and execute the appropriate flow based on status."""
        try:
            tab = self.detect_tab()

            # No results: hop from LIVE → HISTORY, otherwise nothing to do
            if status == SearchStatus.NONE:
                logging.debug("No records in current tab.")
                if tab == TabContext.LIVE:
                    logging.debug("Switching to History tab and retrying search.")
                    return self.go_to_history_root(transaction, action, comment)
                logging.debug("Already in History; we go to BPM.")

            # LIVE requires unlocking; HISTORY doesn’t
            if tab == TabContext.LIVE:
                self.unlock_transaction()

            # LIVE uses column 1, HISTORY uses column 2 (0-based)
            tx_col_idx = 1 if tab == TabContext.LIVE else 2
            self.first_row_matches_transaction(transaction, column=tx_col_idx)

            state = self.get_first_row_state(tab)
            logging.debug("Detected transaction state: %s", state)

            if tab == TabContext.HISTORY:
                return state

            # Map states to handlers
            handler = {
                "FILTER": self._handle_filter,
                "CU_FILTER": self._handle_filter,
                "PendingSanctions": self._manager_followup,
                "CU_Pending_Sanct": self._manager_followup,
            }.get(state)

            if not handler:
                # Stop execution on unknown state (as requested)
                raise Exception(
                    f"Unknown transaction status: {state} for transaction: {transaction}"
                )

            return handler(transaction, action, comment, tab)

        except PlaywrightTimeoutError as e:
            logging.error("verify_first_row timed out: %s", e)

    def first_row_matches_transaction(self, transaction: str, column: int) -> bool:
        """Check if the first row's given column equals the transaction."""
        try:
            logging.debug(
                "Checking first-row column %s for transaction: %s", column, transaction
            )
            cell_text = (
                self.selectors.first_row_column_text.nth(column).text_content() or ""
            ).strip()
            if cell_text == transaction:
                logging.debug("Transaction number matches.")
                return True

            logging.error(
                "Transaction mismatch. Expected %s, got %s", transaction, cell_text
            )
            self.page.screenshot(
                path="first_row_matches_transaction.png", full_page=True
            )
            raise AssertionError(
                f"Transaction mismatch. Expected {transaction}, got {cell_text}"
            )
        except PlaywrightTimeoutError as e:
            logging.error("first_row_matches_transaction timeout: %s", e)
            return False

    def get_first_row_state(self, tab: TabContext) -> str:
        """
        LIVE  -> read 'State' column
        HISTORY -> read 'Decision type' column
        """
        logging.debug("Getting first row state for %s tab.", tab.name)
        try:
            state_cell_text = (
                self.selectors.first_row_state_column.text_content() or ""
            ).strip()
            logging.debug("State/Decision content: %s", state_cell_text)
            return state_cell_text
        except Exception as e:
            logging.warning("Unable to read state/decision column content: %s", e)
            return ""

    def unlock_transaction(self):
        """unlock transaction"""
        if self.selectors.first_row_active.is_visible(timeout=0):
            logging.debug("Transaction already unlocked")
            return True

        logging.debug("Unlocking transaction")
        try:
            self.selectors.padlock_icon.click()
            expect(self.selectors.unlock_overlay_titlebar).to_be_visible(timeout=2000)
            expect(self.selectors.close_overlay_button).to_be_visible(timeout=2000)
            self.selectors.close_overlay_button.click()
            logging.debug("Transaction unlocked!")
            return True
        except PlaywrightTimeoutError as e:
            logging.error("unlock_transaction triggered timeout.")
            logging.error("unlock_transaction error: %s", e)
            return False

    def sort_multiple_transactions(self) -> bool:
        """
        Sorts the transactions in descending date order.

        Returns:
            bool: True if sorting was applied successfully.
        """
        try:
            logging.debug("Sorting multiple transactions by descending order.")
            self.selectors.filtered_date_menu_opener.click()
            self.selectors.descending_date.click()
            self.page.screenshot(path="sorted_transactions.png", full_page=True)
            return True
        except PlaywrightTimeoutError as e:
            logging.error("sort_multiple_transactions triggered timeout.")
            logging.error("sort_multiple_transactions error: %s", e)
            return False

    def go_to_transactions_details(self):
        """
        go to transactions details
        click on a first row
        """
        try:
            logging.debug("Navigating to transactions details.")
            self.selectors.first_row_active.click()
            expect(self.selectors.comment_field).to_be_visible(timeout=2000)
            return True
        except PlaywrightTimeoutError as e:
            logging.error("go_to_transactions_details triggered timeout.")
            logging.error("go_to_transactions_details error: %s", e)
            return False

    def click_all_hits(self) -> None:
        """
        Click on all available transaction hit rows and optionally take screenshots.

        """
        try:
            logging.debug("Clicking on all hits.")
            self.page.screenshot(path="hit_0.png", full_page=True)

            rows = self.selectors.transaction_rows.element_handles()

            for i in range(3, len(rows)):
                row = rows[i]
                row.click()
                self.page.screenshot(path=f"hit{i-2}.png", full_page=True)
            logging.debug("All hits clicked.")
            return True
        except PlaywrightTimeoutError as e:
            logging.error("click_all_hits triggered timeout.")
            logging.error("click_all_hits error: %s", e)
            return False

    def fill_comment_field(self, text: str):
        """
        Fill the transaction comment field with the provided text.

        Args:
            text: The comment text to enter
        """
        try:
            logging.debug("Filling comment field with text: %s", text)
            if text == "":
                text = "No comment provided"
            expect(self.selectors.comment_field).to_be_visible()
            self.selectors.comment_field.fill(text)
            return True
        except PlaywrightTimeoutError as e:
            logging.error("fill_comment_field triggered timeout.")
            logging.error("fill_comment_field error: %s", e)
            return False

    def perform_action(self, action: str):
        """performing action"""
        action_button_map = {
            "STP-Release": self.selectors.stp_release,
            "Release": self.selectors.release,
            "Block": self.selectors.block,
            "Reject": self.selectors.reject,
        }

        if action in action_button_map:
            try:
                # Convert action name to lowercase for screenshot naming
                action_name = action.lower().replace("-", "_")

                # Take screenshot before action
                self.page.screenshot(path=f"{action_name}_1.png", full_page=True)
                logging.debug("Taking screenshot before %s action", action_name)

                # Click the action button
                logging.debug("Clicking %s button", action_name)
                action_button_map[action].click()

                # Take screenshot after action button click
                self.page.screenshot(path=f"{action_name}_2.png", full_page=True)
                logging.debug("Taking screenshot after %s button click", action_name)

                # Click confirm button
                logging.debug("Clicking Confirm button")
                self.selectors.confirm.click()

                # Take screenshot after confirmation
                self.page.screenshot(path=f"{action_name}_3.png", full_page=True)
                logging.debug("%s action confirmed", action_name)
            except PlaywrightTimeoutError as e:
                logging.error("perform_action triggered timeout.")
                logging.error("perform_action error: %s", e)
        else:
            logging.warning(
                "Action '%s' not recognized. Available actions: %s",
                action,
                ", ".join(action_button_map.keys()),
            )

    def _prepare_details_and_comment(self, comment: str) -> None:
        """Open details, select all hits, and fill the comment."""
        try:
            logging.debug("Preparing details and comment.")
            self.go_to_transactions_details()
            self.click_all_hits()
            self.fill_comment_field(comment)
        except PlaywrightTimeoutError as e:
            logging.error("_prepare_details_and_comment triggered timeout.")
            logging.error("_prepare_details_and_comment error: %s", e)

    def _manager_followup(
        self, transaction: str, action: str, comment: str, tab: TabContext
    ) -> bool:
        """Single place for the manager flow."""
        try:
            logging.debug("Running manager flow.")
            self.logout()
            login_to(self.page, TEST_URL, MANAGER_USERNAME, MANAGER_PASSWORD)
            self.go_to_live_messages_root()
            self.clear_filtered_column()
            self.data_filters(transaction)
            self._prepare_details_and_comment(comment)
            if action == "STP-Release":
                action = "Release"
            self.perform_action(action)
            self.logout()
            return True
        except PlaywrightTimeoutError as e:
            logging.error("_manager_followup triggered timeout.")
            logging.error("_manager_followup error: %s", e)
            return False

    def _handle_filter(
        self, transaction: str, action: str, comment: str, tab: TabContext
    ) -> bool:
        """FILTER / CU_FILTER."""
        try:
            logging.debug("Running filter flow.")
            self._prepare_details_and_comment(comment)
            if action == "STP-Release":
                self.perform_action(action)
                self.logout()
                return True
            # escalate then manager flow
            self.selectors.escalate.click()
            return self._manager_followup(transaction, action, comment, tab)
        except PlaywrightTimeoutError as e:
            logging.error("_handle_filter_like triggered timeout.")
            logging.error("_handle_filter_like error: %s", e)
            return False

    def flow_start(
        self, transaction: str, action: str, comment: str, transaction_type: str = ""
    ) -> dict:
        """Start the flow and return a structured result dict."""
        logging.debug("Starting flow")
        logging.debug("for transaction: %s", transaction)
        logging.debug("with action: %s", action)
        logging.debug("with comment: %s", comment)
        logging.debug("with transactionType: %s", transaction_type)

        self._clear_existing_screenshots()

        result: dict = {
            "transaction": transaction,
            "action": action,
            "success": False,
            "status": "processing_error",
            "message": "",
            "error_code": 500,
            "screenshot_path": None,
            "transactionType": transaction_type,
        }

        try:
            login_to(self.page, TEST_URL, USERNAME, PASSWORD)
            self.go_to_live_messages_root()
            self.clear_filtered_column()
            self.data_filters(transaction)
            status = self.validate_search_table_results()
            handled = self.verify_first_row(transaction, status, action, comment)

            # Build success message based on outcome
            if handled is True:
                result["success"] = True
                result["status"] = (
                    "action_performed_on_live"
                    if self.detect_tab() == TabContext.LIVE
                    else "already_handled"
                )
                result["message"] = (
                    f"Transaction {transaction} processed successfully (status: {result['status']})."
                )
                result["error_code"] = 0
            elif isinstance(handled, str):
                # When verify_first_row returns a state string (e.g., FILTER/CU_FILTER/HISTORY state)
                result["success"] = True
                result["status"] = handled
                result["message"] = (
                    f"Transaction {transaction} processed with state: {handled}."
                )
                result["error_code"] = 0
            else:
                result["success"] = False
                result["status"] = "processing_error"
                result["message"] = f"Transaction {transaction} failed to process."
                result["error_code"] = 500
        except PlaywrightTimeoutError as e:
            logging.error("flow_start triggered timeout.")
            logging.error("flow_start error: %s", e)
            result["success"] = False
            result["message"] = str(e)
            result["error_code"] = 504
        finally:
            try:
                archived = self._archive_screenshots(transaction)
                result["screenshot_path"] = str(archived) if archived else None
            except Exception as e:
                logging.error("_archive_screenshots error: %s", e)
        return result

    def _archive_screenshots(self, transaction: str) -> Optional[Path]:
        """Delegate to shared utility to archive screenshots for the transaction."""
        return archive_screenshots(transaction)

    def _clear_existing_screenshots(self) -> None:
        """Delegate to shared utility to clear screenshots in CWD."""
        clear_existing_screenshots()
