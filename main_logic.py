import os
import logging
import shutil
import time
import json
import sys
from datetime import datetime
from playwright.sync_api import Page, expect, sync_playwright
from FircoPage import FircoPage, TransactionError

# Import helper functions from utils.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import parse_txt_file, create_output_structure, move_screenshots_to_folder, get_txt_files

# --- Config ---
INCOMING_DIR = "input"
OUTPUT_DIR = "output"
LOG_FILE = "transactions.log"
TEST_URL = "https://example.com"
USERNAME = "user"
PASSWORD = "pass"
MANAGER_USERNAME = "manager"
MANAGER_PASSWORD = "pass"

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
    logging.info(f"Logging to Firco as {username}.")
    page.goto(url)
    expect(page).to_have_title("State Street Login")
    page.fill("input[name='username']", username)
    page.fill("input[name='PASSWORD']", password)
    page.click("input[type='submit'][value='Submit']")
    page.wait_for_load_state("networkidle")
    logging.info(f"We are in Firco as {username}.")

# --- Firco Transaction Processing ---
def process_firco_transaction(page, transaction, action, user_comment, needs_escalation=False):
    """
    Process a Firco transaction with the specified action.
    
    Args:
        page: The Playwright page object
        transaction: Transaction ID to process
        action: Action to perform (e.g., "STP-Release")
        user_comment: Comment to add to the transaction
        needs_escalation: If True, will escalate and then logout
    
    Returns:
        True if escalation was performed and manager processing is needed
    """
    fircoPage = FircoPage(page)
    fircoPage.go_to_transaction_details(transaction, user_comment)
    
    if action == "STP-Release":
        fircoPage.perform_action(action)
        fircoPage.logout()
        return False
    elif needs_escalation:
        # First user escalates
        fircoPage.escalateBtn.click()
        time.sleep(2)  # Wait for escalation to complete
        fircoPage.logout()
        return True
    else:
        # Manager performs the action after escalation
        fircoPage.perform_action(action)
        fircoPage.logout()
        return False

# --- Transaction Processor ---
def process_transaction(playwright, txt_path):
    transaction, action, user_comment = parse_txt_file(txt_path)
    transaction_folder, date_folder = create_output_structure(transaction, OUTPUT_DIR)

    browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.new_page()
    
    result = {
        'success': False,
        'message': '',
        'error_code': None,
        'screenshot_path': None
    }

    try:
        # First user login and process
        login_to_firco(page, url=TEST_URL, username=USERNAME, password=PASSWORD)
        
        needs_manager = False
        if action != "STP-Release":
            # For non-STP actions, we need escalation and manager processing
            needs_manager = process_firco_transaction(page, transaction, action, user_comment, needs_escalation=True)
        else:
            # For STP-Release, just process directly
            process_firco_transaction(page, transaction, action, user_comment)
        
        # If escalation was performed, do manager processing
        if needs_manager:
            login_to_firco(page, url=TEST_URL, username=MANAGER_USERNAME, password=MANAGER_PASSWORD)
            process_firco_transaction(page, transaction, action, user_comment)

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
        
        # Set success result
        result['success'] = True
        result['message'] = f"Successfully processed transaction: {transaction}"

    except TransactionError as te:
        # Handle specific transaction errors with detailed information
        logging.error(f"Transaction error processing {transaction}: {te}")
        result['success'] = False
        result['message'] = te.message
        result['error_code'] = te.error_code
        result['screenshot_path'] = te.screenshot_path
        
        # Log the error to the transaction history
        error_msg = f"ERROR {te.error_code}: {transaction}, action: {action}, error: {te.message}"
        with open(os.path.join(OUTPUT_DIR, "error_log.txt"), "a") as log:
            log.write(error_msg + "\n")
            
    except Exception as e:
        # Handle generic errors
        logging.error(f"Failed processing {transaction}: {e}")
        result['success'] = False
        result['message'] = str(e)
        result['error_code'] = 500
    finally:
        # Make sure browser is closed even if there's an error
        if 'page' in locals() and page:
            try:
                page.close()
            except:
                pass
        if 'browser' in locals() and browser:
            try:
                browser.close()
            except:
                pass
    
    # Return the result as JSON string for the server to use
    return json.dumps(result)

# --- Main Execution ---
def main():
    setup_logging()
    logging.info("Script started")

    with sync_playwright() as p:
        for txt_file in get_txt_files(INCOMING_DIR):
            txt_path = os.path.join(INCOMING_DIR, txt_file)
            result = process_transaction(p, txt_path)
            print(result)

if __name__ == "__main__":
    main()
