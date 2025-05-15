import logging
from enum import Enum
from playwright.sync_api import expect, Page


class Options(Enum):
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
    def __init__(self, page: Page):
        self.page = page
        self.menu_item = page.locator("div.modal-content[role='document']")

    def safe_click(self, locator, description: str):
        if locator.is_visible():
            locator.click()
            logging.info(f"Clicked on {description}.")
        else:
            msg = f"{description} is not visible."
            logging.error(msg)
            raise Exception(msg)

    def login(self, url: str, username: str, password: str) -> None:
        try:
            logging.info("Logging to BPM as %s.", username)
            self.page.goto(url)
            expect(self.page).to_have_title("State Street Login")
            self.page.fill("input[name='username']", username)
            self.page.fill("input[name='PASSWORD']", password)
            self.page.click("input[type='submit'][value='Submit']")
            self.page.wait_for_load_state("networkidle")

            title = self.page.title()
            if title == "State Street Corporation":
                logging.info("Successfully logged in to BPM as %s.", username)
            elif title == "State Street Login":
                raise Exception("Login failed: Invalid credentials.")
            else:
                raise Exception("Login failed: Unexpected page title.")

        except Exception as e:
            logging.error("Failed to login to BPM: %s", e)
            raise

    def verify_modal_visibility(self) -> None:
        try:
            if self.menu_item.is_visible():
                logging.info("<div class='modal-content' role='document'> is visible.")
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
            for option in options:
                option_locator = self.page.locator(
                    f"li span.inf-name:has-text('{option.value}') i.fa-square-o"
                )
                self.safe_click(option_locator, f"option '{option.value}'")
        except Exception as e:
            logging.error("Failed to check specified options in the list: %s", e)
            raise

    def click_submit_button(self) -> None:
        try:
            self.page.click("button.btn.btn-primary")
            logging.info("Clicked on the Submit button.")
        except Exception as e:
            logging.error("Failed to click on the Submit button: %s", e)
            raise

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
                    logging.info(
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

    def select_all_from_dropdown(self) -> None:
        try:
            dropdown = self.page.locator("select")
            dropdown.wait_for(state="visible", timeout=5000)
            self.safe_click(dropdown, "'ALL' dropdown")
            dropdown.select_option(value="ALL")
            logging.info("Selected 'ALL' from the dropdown.")
        except Exception as e:
            logging.error("Failed to select 'ALL' from the dropdown: %s", e)
            raise

    def wait_for_page_to_load(self) -> None:
        try:
            self.page.wait_for_load_state("networkidle")
            logging.info("Page has finished loading.")
        except Exception as e:
            logging.error("Failed to wait for the page to finish loading: %s", e)
            raise

    def look_for_number(self, number: str) -> tuple:
        try:
            number_element = self.page.locator(f"div.tcell[title='{number}']")
            if number_element.is_visible():
                logging.info(f"Found the number: {number}")
                number_element.evaluate(
                    "element => element.scrollIntoView({block: 'center', inline: 'center'})"
                )
                parent_row = number_element.locator(
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
