import logging
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from enum import Enum, auto


class TransactionError(Exception):
    """Custom exception for transaction processing errors with error codes and detailed messages."""

    def __init__(self, message, error_code, screenshot_path=None):
        self.message = message
        self.error_code = error_code
        self.screenshot_path = screenshot_path
        super().__init__(f"Error {error_code}: {message}")


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
        self.filtered_column_icon = page.locator("a.column-filtered-icon")

        # Search selectors
        self.menu_opener = page.locator("#fmf-table-column-message-id-col-menu-opener")
        self.input_field = page.locator("input.quick-filter-input")
        self.search_btn = page.locator("div.quick-filter-icon")
        self.no_data_notice = page.locator("div.no-data-notice")
        self.first_odd_row_td_text = (
            page.locator("tr.odd-row").first.locator("td").first
        )
        self.first_row = page.locator("tr.even-row.clickable-row")
        self.comment_field = page.locator(
            "textarea.stick.ui-autocomplete-input[name='COMMENT']"
        )
        self.table = page.locator("table.hit-table.live tbody tr")

        # Action buttons
        self.stp_release = page.locator("input[value='STP_Release']")
        self.confirm = page.locator("input#Confirm\\ Button")
        self.release = page.locator("input[value='Release']")
        self.reject = page.locator("input[value='Reject']")
        self.block = page.locator("input[value='Block']")
        self.logout = page.locator("#logout-button")
        self.escalate = page.locator("input[value='Esc_Sanctions']")


class SearchStatus(Enum):
    NONE = auto()
    MULTIPLE = auto()
    FOUND = auto()


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
        self.page = page
        self.sel = Selectors(page)  # Group all selectors in a separate object

    def clear_filtered_column(self):
        """
        Clear any filters that may be applied to the transaction column.

        Checks if a filter icon is visible and clicks it if present.
        """
        if self.sel.filtered_column_icon.is_visible(timeout=60000):
            self.sel.filtered_column_icon.click()
        else:
            logging.info("No filter in transaction column.")

    def search_transaction(self, transaction: str):
        """
        Search for a specific transaction by ID.

        Args:
            transaction: The transaction ID to search for
        """
        self.sel.menu_opener.click()
        self.sel.input_field.fill(transaction)
        self.sel.search_btn.click()
        try:
            self.page.wait_for_selector(".loading-indicator", state="visible")
            self.page.wait_for_selector(
                ".loading-indicator", state="hidden", timeout=5000
            )
        except PlaywrightTimeoutError as e:
            logging.error("Timeout waiting for loading indicator: %s", e)
        except (ValueError, RuntimeError) as e:
            logging.error("Error while waiting for loading indicator: %s", e)

    def go_to_transaction_details(self, transaction: str, comment: str):
        """
        Navigate to a specific transaction's details page.
        """
        self.sel.menu_item.click()
        expect(self.sel.live_messages).to_contain_text("Live Messages")
        try:
            expect(self.sel.live_messages_tab).to_be_visible()
            expect(self.sel.live_messages_tab).to_have_class(
                r"tab-center tab-center-selected"
            )
        except (AssertionError, PlaywrightTimeoutError) as e:
            logging.info("Live Messages tab not active: %s", e)
            logging.info("Clicking on Live Messages tab.")
            self.sel.live_messages_tab.click()
            expect(self.sel.live_messages_tab).to_have_class(
                r"tab-center tab-center-selected"
            )

        # 1) search in Live Messages tab
        self.clear_filtered_column()
        self.search_transaction(transaction)
        status = self.verify_search_results(transaction)
        initial_status = status

        if status == SearchStatus.NONE:
            # History tab
            self.sel.history_item.click()
            # self.page.wait_for_load_state("networkidle")
            # self.clear_filtered_column()
            self.search_transaction(transaction)
            status = self.verify_search_results(transaction)
            print(status)

        if status == SearchStatus.NONE:
            # BPM placeholder
            status = self.verify_on_bpm(transaction)

        if status == SearchStatus.NONE:
            raise TransactionError(f"{transaction} not found in any tab", 404)
        if status == SearchStatus.MULTIPLE:
            raise TransactionError(
                f"Multiple transactions found for ID: {transaction}", 409
            )

        if initial_status == SearchStatus.FOUND:
            self.fill_comment_field(comment)
            self.click_all_hits(True)

    def click_all_hits(self, screenshots: bool):
        """
        Click on all available transaction hit rows and optionally take screenshots.

        Args:
            screenshots: If True, take screenshots after each click
        """
        if screenshots:
            self.page.screenshot(path="hit_0.png", full_page=True)

        rows = self.sel.table.all()

        for i in range(3, len(rows)):
            row = rows[i]
            try:
                row.click()
                if screenshots:
                    self.page.screenshot(path=f"hit{i-2}.png", full_page=True)
            except PlaywrightTimeoutError as e:
                logging.error("Timeout when clicking row %d: %s", i, e)
            except (ValueError, TypeError) as e:
                logging.error("Invalid parameter when clicking row %d: %s", i, e)
            except RuntimeError as e:
                logging.error("Runtime error when clicking row %d: %s", i, e)

    def verify_search_results(self, transaction: str) -> SearchStatus:
        """
        Verify search results for a transaction and return status.
        """
        if self.sel.no_data_notice.is_visible():
            self.page.screenshot(path="noTransactions.png", full_page=True)
            return SearchStatus.NONE

        if (self.sel.first_odd_row_td_text.text_content() or "").strip():
            self.page.screenshot(path="moreTransactions.png", full_page=True)
            return SearchStatus.MULTIPLE

        self.page.screenshot(path="transaction_one.png", full_page=True)
        try:
            self.sel.first_row.click()
        except Exception as e:
            screenshot_path = "transaction_notActive.png"
            self.page.screenshot(path=screenshot_path, full_page=True)
            raise TransactionError(
                f"Transaction {transaction} found but cannot be selected: {str(e)}",
                error_code=422,
                screenshot_path=screenshot_path,
            ) from e

        return SearchStatus.FOUND

    def verify_on_bpm(self, transaction: str) -> SearchStatus:
        """
        Placeholder for BPM page search.
        """
        # TODO: implement BPM search logic
        return SearchStatus.NONE

    def fill_comment_field(self, text: str):
        """
        Fill the transaction comment field with the provided text.

        Args:
            text: The comment text to enter
        """
        expect(self.sel.comment_field).to_be_visible()
        self.sel.comment_field.fill(text)

    def logout(self):
        """
        Log out from the Firco system.

        Waits for a brief timeout to ensure all actions are complete,
        then clicks the logout button and logs the action.
        """
        self.page.wait_for_timeout(2000)
        self.sel.logout.click()
        logging.info("logged out!")

    def perform_action(self, action: str):
        """
        Perform a specified action on the current transaction.

        Takes screenshots before and after each step of the action,
        clicks the appropriate button for the action, and confirms it.

        Args:
            action: The action to perform (STP-Release, Release, Block, or Reject)
        """
        action_button_map = {
            "STP-Release": self.sel.stp_release,
            "Release": self.sel.release,
            "Block": self.sel.block,
            "Reject": self.sel.reject,
        }

        if action in action_button_map:
            # Convert action name to lowercase for screenshot naming
            action_name = action.lower().replace("-", "_")

            # Take screenshot before action
            self.page.screenshot(path=f"{action_name}_1.png", full_page=True)

            # Click the action button
            action_button_map[action].click()

            # Take screenshot after action button click
            self.page.screenshot(path=f"{action_name}_2.png", full_page=True)

            # Click confirm button
            self.sel.confirm.click()

            # Take screenshot after confirmation
            self.page.screenshot(path=f"{action_name}_3.png", full_page=True)
        else:
            logging.warning(
                "Action '%s' not recognized. Available actions: %s",
                action,
                ", ".join(action_button_map.keys()),
            )
