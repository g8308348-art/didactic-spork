import os
import logging
import shutil
from datetime import datetime
from playwright.sync_api import Page, expect, sync_playwright
from FircoPage import FircoPage

# --- Config ---
INCOMING_DIR = "input"
OUTPUT_DIR = "output"
LOG_FILE = "trasactions.log"
TEST_URL = "https://example.com"
USERNAME = "user"
PASSWORD = "pass"

# --- Logging Setup ---
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(msecs)03d] :: %(levelname)s :: %(name)s :: %(funcName)s :: %(message)s",
        datefmt="%X",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

# --- Firco Login ---
def login_to_firco(page: Page, url=TEST_URL, username=USERNAME, password=PASSWORD):
    logging.info("Logging to Firco.")
    page.goto(url)
    expect(page).to_have_title("State Street Login")
    page.fill("input[name='username']", username)
    page.fill("input[name='PASSWORD']", password)
    page.click("input[type='submit'][value='Submit']")
    page.wait_for_load_state("networkidle")
    logging.info("We are in Firco.")

# --- Firco Transaction Processing ---
def process_firco_transaction(fircoPage, transaction, action, user_comment):
    fircoPage.go_to_transaction_details(transaction, user_comment)
    if action == "STP-RELEASE":
        fircoPage.perform_action(action)
    else:
        fircoPage.escalateBtn.click()
    fircoPage.logout()

# --- Transaction Processor ---
def process_transaction(playwright, txt_path):
    transaction, action, user_comment = parse_txt_file(txt_path)
    transaction_folder, date_folder = create_output_structure(transaction)

    browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.new_page()

    try:
        login_to_firco(page)
        fircoPage = FircoPage(page)
        process_firco_transaction(fircoPage, transaction, action, user_comment)

        try:
            move_screenshots_to_folder(date_folder)
        except Exception as e:
            logging.error("102 FU")
            logging.error(e)

        try:
            os.rename(txt_path, os.path.join(transaction_folder, os.path.basename(txt_path)))
        except Exception as e:
            logging.error("108 FU")
            logging.error(e)

        msg = f"Processed transaction: {transaction}, action: {action}, user: {user_comment}"
        with open(os.path.join(OUTPUT_DIR, "daily_log.txt"), "a") as log:
            log.write(msg + "\n")
        logging.info(msg)

    except Exception as e:
        logging.error(f"Failed processing {transaction}: {e}")
    finally:
        browser.close()

# --- Main Execution ---
def main():
    setup_logging()
    logging.info("Script started")

    with sync_playwright() as p:
        for txt_file in get_txt_files(INCOMING_DIR):
            txt_path = os.path.join(INCOMING_DIR, txt_file)
            process_transaction(p, txt_path)

if __name__ == "__main__":
    main()
