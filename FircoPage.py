import logging
from playwright.sync_api import Page, expect

class FircoPage:
    def __init__(self, page: Page):
        self.page = page
        self.menuItemSelector = page.locator('li#root-menu-0')
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
        if self.filteredColumnIcon.is_visible(timeout=60000):
            self.filteredColumnIcon.click()
        else:
            logging.info("No filter in transaction column.")

    def search_transaction(self, transaction: str):
        self.menuOpenerSelector.click()
        self.inputFileSelector.fill(transaction)
        self.searchTransactionBtn.click()
        try:
            self.page.wait_for_selector(".loading-indicator", state="visible")
            self.page.wait_for_selector(".loading-indicator", state="hidden", timeout=5000)
        except:
            logging.error("didn't catch the loading indicator")

    def go_to_transaction_details(self, transaction: str, comment: str):
        self.menuItemSelector.click()
        expect(self.liveMessagesSelector).to_contain_text("Live Messages")

        try:
            expect(self.liveMessagesTab).to_be_visible()
            expect(self.liveMessagesTab).to_have_class(r"tab-center tab-center-selected")
        except:
            logging.info("Live Messages tab not active.")
            logging.info("Clicking on Live Messages tab.")
            self.liveMessagesTab.click()
            expect(self.liveMessagesTab).to_have_class(r"tab-center tab-center-selected")

        self.clear_filtered_column()
        self.search_transaction(transaction)
        self.verify_search_results(transaction)
        self.fill_comment_field(comment)
        self.click_all_hits(transaction, True)

    def click_all_hits(self, transaction: str, screenshots: bool):
        if screenshots:
            self.page.screenshot(path="git_0.png", full_page=True)

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
        if self.noDataNotice.is_visible():
            self.page.screenshot(path="noTransactions.png", full_page=True)
            raise Exception("No transaction found!")

        odd_row_text = (self.firstOddRow_tdText.text_content() or "").strip()

        if odd_row_text:
            self.page.screenshot(path="moreTransactions.png", full_page=True)
            raise Exception("More than one transaction found!")

        self.page.screenshot(path="transaction_one.png", full_page=True)

        try:
            self.firstRowSelector.click()
        except:
            self.page.screenshot(path="transaction_notActive.png", full_page=True)
            raise Exception("transaction not active!")

    def fill_comment_field(self, text: str):
        expect(self.commentField).to_be_visible()
        self.commentField.fill(text)

    def logout(self):
        self.page.wait_for_timeout(2000)
        self.logoutBtn.click()
        logging.info("logged out!")

    def perform_action(self, action: str):
        if action == "STP-RELEASE":
            self.page.screenshot(path="stp_release_1.png", full_page=True)
            self.stpReleaseBtn.click()
            self.page.screenshot(path="stp_release_2.png", full_page=True)
            # self.confirmBtn.click()
            # self.page.screenshot(path="stp_release_3.png", full_page=True)
        else:
            logging.info("not implemented yet")
