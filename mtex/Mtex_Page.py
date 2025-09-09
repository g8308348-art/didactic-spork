import logging
from enum import Enum
from typing import Union
from playwright.sync_api import expect, Page


class BUWorkFlow(Enum):
    ORI_TSF_RTPS_SRCBYP_FED_SSB = "ORI - TSF RTPS SRCBYP FED SSB"
    ORI_TSF_APS = "ORI - TSF APS"
    ORI_TSF_GBM_HK_CHATS = "ORI - TSF GBM HK CHATS"
    ORI_TSF_RTPS_SRCBYP_HK_CHATS = "ORI - TSF RTPS SRCBYP HK CHATS"
    ORI_TSF_GBM_CBPR_OUTBOUND = "ORI - TSF GBM CBPR Outbound"
    ORI_TSF_BESS_AAP = "ORI - TSF BESS AAP"
    ORI_TSF_GBM_CHIPS_FED_SSI = "ORI - TSF GBM CHIPS-FED SSI"
    ORI_TSF_GBM_CBPR = "ORI - TSF GBM CBPR"
    ORI_TSF_GBM_RITS = "ORI - TSF GBM RITS"
    ORI_TSF_GBM_LYNX = "ORI - TSF GBM LYNX"
    ORI_TSF_GBM_CHAPS = "ORI - TSF GBM CHAPS"
    ORI_TSF_GBM_FED_SSB = "ORI - TSF GBM FED SSB"
    ORI_TSF_PEP_WHRS_UA2 = "ORI - TSF PEP+ WHSR UA2"
    ORI_TSF_HOTSCAN_UA2 = "ORI - TSF HotScan UA2"
    ORI_TSF_GBM_TAIWAN = "ORI - TSF GBM Taiwan"
    ORI_TSF_BYPASS_TRIGGER = "ORI - TSF Bypass trigger file generation"
    ORI_TSF_GBM_SEPA_CLASSIC = "ORI - TSF GBM SEPA Classic"
    ORI_TSF_FEDLINE = "ORI - TSF - Fedline"
    ORI_TSF_BYPASS_RESPONSE = "ORI - TSF Bypass response"
    ORI_TSF_GBM_T2S = "ORI - TSF GBM T2S"
    ORI_TSF_RTPS_SRCBYP_T2S = "ORI - TSF RTPS SRCBYP T2S"
    ORI_TSF_RTPS_SRCBYP_RITS = "ORI - TSF RTPS SRCBYP RITS"
    ORI_TSF_RTPS_SRCBYP_LYNX = "ORI - TSF RTPS SRCBYP LYNX"
    ORI_TSF_RTPS_SRCBYP_CHAPS = "ORI - TSF RTPS SRCBYP CHAPS"
    ORI_TSF_PEP_ASAP = "ORI - TSF PEP+ ASAP"
    ORI_TSF_PEP_WHRS = "ORI - TSF PEP+ WHSR"
    ORI_TSF_HOTSCAN = "ORI - TSF HotScan"
    ORI_TSF_PEP_ASAP_UA2 = "ORI - TSF PEP+ ASAP UA2"
    ORI_TSF_RTPS_SRCBYP_TAIWAN = "ORI - TSF RTPS SRCBYP Taiwan"
    ORI_TSF_RTPS_SRCBYP_CHIPS_FED_SSI = "ORI - TSF RTPS SRCBYP CHIPS-FED SSI"
    ORI_TSF_DEH_ISO = "ORI - TSF DEH ISO"
    ORI_TSF_GBM_SEPA = "ORI - TSF GBM SEPA"
    STAR = "ORI - STAR"
    ORI_TSF_BRDCHK_TRIGGER = "ORI - TSF Brdchk Resp Trigger"
    ORI_TSF_BYPASS_UPDATE_DB = "ORI - TSF-BYPASS - update DB status"


class MtexPage:
    def __init__(self, page: Page):
        self.page = page

    def select_dropdown_option(
        self, dropdown_id: str, option_title: Union[str, BUWorkFlow]
    ) -> None:
        """Select an option from a dropdown with detailed error handling."""
        try:
            title = (
                option_title.value
                if isinstance(option_title, BUWorkFlow)
                else option_title
            )
            logging.debug("Selecting dropdown %s with title '%s'", dropdown_id, title)

            # Click to open dropdown
            self.page.click(f"input[id='{dropdown_id}']", timeout=5000)
            logging.debug("Dropdown opened for %s", dropdown_id)

            # Click the option
            self.page.click(f"div[title='{title}']", timeout=5000)
            logging.info("Selected option '%s' from dropdown '%s'.", title, dropdown_id)
        except Exception as e:
            logging.error(
                "Failed to select option '%s' from dropdown '%s': %s",
                option_title,
                dropdown_id,
                e,
            )
            raise ValueError(f"Dropdown selection failed for {dropdown_id} -> {option_title}: {e}") from e

    def upload_files_and_click_button(
        self, file_input_selector: str, file_paths: list, button_selector: str
    ) -> None:
        """Upload files and click the button with detailed error handling."""
        try:
            logging.debug("Uploading files to selector '%s': %s", file_input_selector, file_paths)
            self.page.set_input_files(file_input_selector, file_paths, timeout=10000)
            logging.info("Files uploaded successfully: %s", file_paths)

            logging.debug("Clicking button with selector '%s'", button_selector)
            self.page.click(button_selector, timeout=5000)
            logging.info("Clicked the upload button successfully.")
        except Exception as e:
            logging.error("Failed to upload files and click button: %s", e)
            raise ValueError(f"File upload failed: {e}") from e
