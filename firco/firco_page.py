""" firco page POM"""

import logging
from enum import Enum, auto
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


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
        self.table_rows_first_message_id_cell = self.table_rows_first.locator("td").nth(
            1
        )

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
    ALREADY_ESCALATED = auto()


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
        logging.info("FircoPage.__init__ called")
        self.page = page
        self.selectors = Selectors(page)  # Group all selectors in a separate object

    def login_to_firco(
        self,
        url: str,
        username: str,
        password: str,
    ) -> bool:
        """
        Login to the Firco system.

        Args:
            page: The Playwright page object
            url: The URL of the Firco system
            username: Login username
            password: Login password
        """
        logging.info("Logging to Firco as %s.", username)
        self.page.goto(url)
        expect(self.page).to_have_title("State Street Login")
        self.page.fill("input[name='username']", username)
        self.page.fill("input[name='PASSWORD']", password)
        self.page.click("input[type='submit'][value='Submit']")
        self.page.wait_for_load_state("networkidle")
        try:
            expect(self.selectors.logout).to_be_visible()
            logging.info("We are in Firco as %s.", username)
            return True
        except Exception as e:
            logging.error("Failed to login to Firco as %s", username)
            logging.error("Login error: %s", e)
            return False

    def logout(self) -> bool:
        """
        Log out from the Firco system.

        Waits for a brief timeout to ensure all actions are complete,
        then clicks the logout button and logs the action.
        """
        self.page.wait_for_timeout(2000)
        self.selectors.logout.click()
        logging.info("logged out!")
        return True

    def go_to_live_messages_root(self) -> bool:
        """
        Go to the Live Messages root page.
        """
        logging.info("Navigating to live messages link!")
        # self.sel.menu_item.click()
        self.selectors.live_messages_link.click()

        expect(self.selectors.live_messages).to_contain_text("Live Messages")

        try:
            expect(self.selectors.live_messages_tab).to_be_visible()
            expect(self.selectors.live_messages_tab).to_have_class(
                r"tab-center tab-center-selected"
            )
        except (AssertionError, PlaywrightTimeoutError) as e:
            logging.info("Live Messages tab not active: %s", e)
            logging.info("Clicking on Live Messages tab.")
            self.selectors.live_messages_tab.click()
            expect(self.selectors.live_messages_tab).to_have_class(
                r"tab-center tab-center-selected"
            )
        return True
