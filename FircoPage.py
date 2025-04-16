import logging
from playwright.sync_api import Page, expect

class TransactionError(Exception):
    """Custom exception for transaction processing errors with error codes and detailed messages."""
    def __init__(self, message, error_code, screenshot_path=None):
        self.message = message
        self.error_code = error_code
        self.screenshot_path = screenshot_path
        super().__init__(f"Error {error_code}: {message}")


class FircoPage:
    """
    Page Object Model for interacting with the Firco transaction processing UI.
    Encapsulates browser automation actions for searching, verifying, and processing transactions.
    """
    def __init__(self, page: Page):
        """
        Initialize FircoPage with Playwright Page instance and set up selectors.
        
        Args:
            page (Page): Playwright Page object representing the browser context.
        """
        self.page = page
        self.mainLiveMessagesSelector = page.locator('li#root-menu-0')
        self.historyLiveMessagesSelector = page.locator('li#root-menu-1')
        self.liveMessagesSelector = page.locator('div.stick#text-element-8')
        self.liveMessagesTab = page.locator("a.tab-center").filter(has_text='Live Messages')
        self.filteredColumnIcon = page.locator('a.column-filtered-icon')
        self.menuOpenerSelector = page.locator('#fmf-table-column-message-id-col-menu-opener')
        self.inputFileSelector = page.locator('input.quick-filter-input')
        self.searchTransactionBtn = page.locator('div.quick-filter-icon')
        self.noDataNotice = page.locator('div.no-data-notice')
        self.firstOddRow_tdText = page.locator('tr.odd-row').first.locator('td').first
        self.firstRowSelector = page.locator('tr.even-row.clickable-row')
        self.commentField = page.locator("textarea.stick.ui-autocomplete-input[name='COMMENT']")
        self.tableSelector = page.locator("table.hit-table.live tbody tr")
        self.stpReleaseBtn = page.locator("input[value='STP_Release']")
        self.confirmBtn = page.locator("input#Confirm\\ Button")
        self.releaseBtn = page.locator("input[value='Release']")
        self.rejectBtn = page.locator("input[value='Reject']")
        self.blockBtn = page.locator("input[value='Block']")
        self.logoutBtn = page.locator("#logout-button")
        self.escalateBtn = page.locator("input[value='Esc_Sanctions']")


    def clear_filtered_column(self):
        """
        Clear any active filter in the transaction column if present.
        """
        if self.filteredColumnIcon.is_visible(timeout=60000):
            self.filteredColumnIcon.click()
        else:
            logging.info("No filter in transaction column.")


    def search_transaction(self, transaction: str):
        """
        Search for a transaction by ID using the filter input and trigger the search.
        
        Args:
            transaction (str): Transaction ID to search for.
        """
        self.menuOpenerSelector.click()
        self.inputFileSelector.fill(transaction)
        self.searchTransactionBtn.click()
        try:
            self.page.wait_for_selector(".loading-indicator", state="visible")
            self.page.wait_for_selector(".loading-indicator", state="hidden", timeout=5000)
        except:
            logging.error("didn't catch the loading indicator")


    def go_to_live_messages(self) -> None:
        """
        Navigate to the live messages tab and prepare for processing.
        """
        self.mainLiveMessagesSelector.click()
        expect(self.liveMessagesSelector).to_contain_text("Live Messages")

        try:
            expect(self.liveMessagesTab).to_be_visible()
            expect(self.liveMessagesTab).to_have_class(r"tab-center tab-center-selected")
        except:
            logging.info("Live Messages tab not active.")
            logging.info("Clicking on Live Messages tab.")
            self.liveMessagesTab.click()
            expect(self.liveMessagesTab).to_have_class(r"tab-center tab-center-selected")


    def click_all_hits(self, transaction: str, screenshots: bool):
        """
        Click all transaction rows (hits) in the table, optionally taking screenshots.
        
        Args:
            transaction (str): Transaction ID being processed.
            screenshots (bool): If True, take screenshots after each click.
        """
        if screenshots:
            self.page.screenshot(path="hit_0.png", full_page=True)

        rows = self.tableSelector.all()

        for i in range(3, len(rows)):
            row = rows[i]
            try:
                row.click()
                if screenshots:
                    self.page.screenshot(path=f"hit{i-2}.png", full_page=True)
            except:
                logging.error("couldn't click row, proceeding")


    def verify_search_results(self, transaction: str):
        """
        Verify search results for a transaction and provide detailed error information.
        
        Args:
            transaction (str): Transaction ID to verify.
        
        Raises:
            TransactionError: If transaction cannot be found, multiple found, or cannot be selected.
        """
        self._check_no_transactions_found(transaction)
        self._check_multiple_transactions_found(transaction)
        self._screenshot_found_transaction()
        self._try_click_transaction_row(transaction)


    def _check_no_transactions_found(self, transaction: str):
        """Raise TransactionError if no transactions are found."""
        if self.noDataNotice.is_visible():
            screenshot_path = "noTransactions.png"
            self.page.screenshot(path=screenshot_path, full_page=True)
            raise TransactionError(
                f"No transaction found for ID: {transaction}",
                error_code=404,
                screenshot_path=screenshot_path
            )

    def _check_multiple_transactions_found(self, transaction: str) -> None:
        """Raise TransactionError if multiple transactions are found."""
        odd_row_text = (self.firstOddRow_tdText.text_content() or "").strip()
        if odd_row_text:
            screenshot_path = "moreTransactions.png"
            self.page.screenshot(path=screenshot_path, full_page=True)
            raise TransactionError(
                f"Multiple transactions found for ID: {transaction}.",
                error_code=409,
                screenshot_path=screenshot_path
            )

    def _screenshot_found_transaction(self) -> None:
        """Take a screenshot of the found transaction."""
        screenshot_path = "transaction_one.png"
        self.page.screenshot(path=screenshot_path, full_page=True)

    def _try_click_transaction_row(self, transaction: str) -> None:
        """Try to click on the transaction row, raise TransactionError if not clickable."""
        try:
            self.firstRowSelector.click()
        except Exception as e:
            screenshot_path = "transaction_notActive.png"
            self.page.screenshot(path=screenshot_path, full_page=True)
            raise TransactionError(
                f"Transaction {transaction} found, but cannot be selected: {str(e)}",
                error_code=422,
                screenshot_path=screenshot_path
            )


    def fill_comment_field(self, text: str) -> None:
        """
        Fill the comment field with the provided text.
        
        Args:
            text (str): Comment to enter in the field.
        """
        expect(self.commentField).to_be_visible()
        self.commentField.fill(text)


    def logout(self) -> None:
        """
        Log out the current user from the Firco application.
        """
        self.page.wait_for_timeout(2000)
        self.logoutBtn.click()
        logging.info("logged out!")


    def perform_action(self, action: str) -> None:
        """
        Perform the specified transaction action (e.g., Release, Block, Reject).
        
        Args:
            action (str): Action to perform. Must be one of 'STP-Release', 'Release', 'Block', or 'Reject'.
        """
        action_button_map = {
            "STP-Release": self.stpReleaseBtn,
            "Release": self.releaseBtn,
            "Block": self.blockBtn,
            "Reject": self.rejectBtn
        }
        
        if action in action_button_map:
            # Convert action name to lowercase for screenshot naming
            action_name = action.lower().replace('-', '_')
            # self.page.screenshot(path=f"{action_name}_1.png", full_page=True)
            action_button_map[action].click()
            # self.page.screenshot(path=f"{action_name}_2.png", full_page=True)
            self.confirmBtn.click()
            # self.page.screenshot(path=f"{action_name}_3.png", full_page=True)
        else:
            logging.info("YOU SHOULD NEVER GET HERE!")
