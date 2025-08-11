"""
Main logic module for processing Firco transactions.

This module contains the core logic for automating transaction processing
in the Firco system, including handling different transaction statuses,
performing actions, and managing user sessions.
"""

import os
import logging
import time
import json
import sys
from dotenv import load_dotenv
from cyber_guard import retrieve_CONTRASENA

# Third-party imports
from playwright.sync_api import Page, expect, sync_playwright

# Local application imports
from firco_page import FircoPage, TransactionError
from utils import (
    parse_txt_file,
    create_output_structure,
    move_screenshots_to_folder,
    get_txt_files,
)

# Load environment variables from .env file if present
load_dotenv()


# --- Constants ---
# Define statuses where no further action (escalate/perform_action) is needed
TERMINAL_READ_ONLY_STATUSES = [
    "already_handled",  # Found in History
    "found_in_sanctions_bypass",  # Found in Sanctions Bypass View
    "found_in_bpm",  # Found in BPM
    "failed_in_bpm",  # BPM search failed
    "action_performed_on_live",  # Action already performed on transaction in Live Messages
    "transaction_not_found_in_any_tab",  # Not found in any tab
]

# Define statuses that indicate the automation step completed successfully
SUCCESSFUL_AUTOMATION_STEP_STATUSES = [
    "action_performed_on_live",  # Action taken on a live item
    "escalated",  # User1 successfully escalated
    "already_handled",  # Found in History, no action needed
    "found_in_bpm",  # Found in BPM, no action needed
    "found_in_sanctions_bypass",  # Found in Sanctions Bypass, no action needed
    "transaction_not_found_in_any_tab",  # Successfully determined not found in any relevant tab
]


# --- Logging Setup ---
def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log"),
        ],
    )


# Add current directory to path to find local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Config (environment overrides .env) ---
INCOMING_DIR = os.getenv("INCOMING_DIR", "input")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOG_FILE = os.getenv("LOG_FILE", "transactions.log")
TEST_URL = os.getenv("TEST_URL", "https://example.com")
USERNAME = "506"
PASSWORD = retrieve_CONTRASENA(USERNAME)
MANAGER_USERNAME = "507"
MANAGER_PASSWORD = retrieve_CONTRASENA(MANAGER_USERNAME)

# Define module-level constants for status strings
TRANSACTION_NOT_FOUND_STATUS = "transaction_not_found_in_any_tab"


# --- Firco Login ---
def login_to_firco(
    page: Page, url: str = TEST_URL, username: str = USERNAME, password: str = PASSWORD
) -> None:
    """
    Login to the Firco system.

    Args:
        page: The Playwright page object
        url: The URL of the Firco system
        username: Login username
        password: Login password
    """
    logging.info("Logging to Firco as %s.", username)
    page.goto(url)
    expect(page).to_have_title("State Street Login")
    page.fill("input[name='username']", username)
    page.fill("input[name='PASSWORD']", password)
    page.click("input[type='submit'][value='Submit']")
    page.wait_for_load_state("networkidle")
    logging.info("We are in Firco as %s.", username)


# --- Firco Transaction Processing ---
def process_firco_transaction(
    page: Page,
    transaction: str,
    action: str,
    user_comment: str,
    transaction_type: str = "",
    needs_escalation: bool = False,
    perform_on_latest: bool = False,
) -> dict:
    """
    Process a Firco transaction with the specified action.
    Returns a dictionary with processing status.
    """
    logging.info("Processing transaction %s with action %s.", transaction, action)
    firco_page = FircoPage(page)

    details_result = firco_page.go_to_transaction_details(
        transaction, user_comment, transaction_type, perform_on_latest
    )
    logging.info(
        "Transaction details result from go_to_transaction_details: %s", details_result
    )

    current_status = details_result.get("status")

    if current_status in TERMINAL_READ_ONLY_STATUSES:
        logging.info(
            "Transaction %s status '%s' requires no further action here.",
            transaction,
            current_status,
        )
        # Only logout from Firco if we're not in BPM (URL doesn't contain 'mtexrt')
        current_url = page.url
        if "mtexrt" not in current_url.lower():
            logging.info("Logging out from Firco for transaction %s.", transaction)
            try:
                firco_page.logout()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logging.warning("Logout failed for status '%s': %s", current_status, e)
        # Return a copy of details_result to ensure consistent return type
        return dict(details_result)

    if "mtexrt" in page.url.lower():
        logging.info(
            "In BPM page (URL contains 'mtexrt'), skipping Firco logout for transaction %s.",
            transaction,
        )

    if current_status == "found_in_live":
        if needs_escalation:
            logging.info(
                "Transaction %s found in Live Messages. Escalating for action '%s'.",
                transaction,
                action,
            )
            firco_page.selectors.escalate.click()
            firco_page.page.wait_for_timeout(1000)
            firco_page.logout()
            return {
                "status": "escalated",
                "message": (
                    f"Transaction {transaction} found in Live Messages and "
                    f"escalated for action '{action}'."
                ),
            }
        # Not needs_escalation, perform direct action
        logging.info(
            "Transaction %s found in Live Messages. Performing action '%s'.",
            transaction,
            action,
        )
        logging.info("Calling perform_action with '%s'", action)
        firco_page.perform_action(action)
        logging.info("perform_action completed, proceeding to logout")
        firco_page.logout()
        return {
            "status": "action_performed_on_live",
            "message": (
                f"Action {action} performed on transaction {transaction} "
                f"found in Live Messages."
            ),
        }
    if (
        current_status not in TERMINAL_READ_ONLY_STATUSES
        and current_status != "found_in_live"
    ):
        logging.warning(
            "Transaction %s not found in Live or History. Attempting BPM search.",
            transaction,
        )
        bpm_result = firco_page.check_bpm_page(transaction, transaction_type)
        return bpm_result

    # If we reach here, it means the status wasn't handled by any of the above conditions
    # This should not happen under normal circumstances, but we need to ensure a return value
    logging.warning(
        "Unexpected state in process_firco_transaction for transaction %s with status %s",
        transaction,
        current_status,
    )
    return {
        "status": "unexpected_state",
        "message": f"Unexpected state for transaction {transaction} with status {current_status}",
    }


# --- Error Handling Functions ---
def cleanup_browser_resources(page: Page = None, context: object = None) -> None:
    """
    Safely close browser resources even if there are exceptions.

    Args:
        page: The Playwright page object
        browser: The Playwright browser object
    """
    # Close page if it exists
    if page:
        try:
            page.close()
        except (OSError, ConnectionError, RuntimeError) as e:
            logging.warning("Failed to close page: %s", e)

    if context:
        try:
            context.close()
        except (OSError, ConnectionError, RuntimeError) as e:
            logging.warning("Failed to close context: %s", e)


def handle_generic_error(transaction: str, error: Exception, result: dict) -> None:
    """
    Handle generic errors during transaction processing.

    Args:
        transaction: The transaction ID
        error: The caught exception
        result: Result dictionary to update
    """
    # Log the error
    logging.error("Failed processing %s: %s", transaction, error)

    # Update result dictionary
    result["success"] = False
    result["message"] = str(error)
    result["error_code"] = 500


def handle_transaction_error(
    transaction: str, action: str, te: TransactionError, result: dict
) -> None:
    """
    Handle specific transaction errors with detailed information.

    Args:
        transaction: The transaction ID
        action: The action being performed
        te: TransactionError exception object
        result: Result dictionary to update
    """
    # Log the error
    logging.error("Transaction error processing %s: %s", transaction, te)

    # Update result dictionary
    result["success"] = False
    result["message"] = te.message
    result["error_code"] = te.error_code
    result["screenshot_path"] = te.screenshot_path

    # Log the error to the transaction history file
    error_msg = (
        f"ERROR {te.error_code}: {transaction}, action: {action}, error: {te.message}"
    )
    with open(os.path.join(OUTPUT_DIR, "error_log.txt"), "a", encoding="utf-8") as log:
        log.write(error_msg + "\n")


# --- Transaction Processor ---
def process_transaction(
    playwright: object,
    txt_path: str,
    transaction_type: str = "",
    perform_on_latest: bool = False,
) -> str:
    """
    Process a transaction from a text file and return the result as JSON.

    Args:
        playwright: The Playwright instance
        txt_path: Path to the transaction text file

    Returns:
        JSON string with the processing result
    """
    transaction, action, user_comment = parse_txt_file(txt_path)
    # transaction_type is now received from server.py and passed in
    transaction_folder, date_folder = create_output_structure(transaction, OUTPUT_DIR)

    # Check if folder creation was successful
    if transaction_folder is None or date_folder is None:
        logging.error(
            "Failed to create output folders for transaction: %s", transaction
        )
        return json.dumps(
            {
                "success": False,
                "message": "Failed to create output folders",
                "error_code": 500,
                "screenshot_path": None,
                "status_detail": "unknown",
            }
        )

    # browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    context = browser.new_context()
    page = context.new_page()

    result = {
        "success": False,
        "message": "",
        "error_code": None,
        "screenshot_path": None,
        "status_detail": "unknown",  # Initialize with a default
    }

    try:
        # I would like to log all the transaction info
        logging.info("Processing transaction: %s", transaction)
        logging.info("Transaction type: %s", transaction_type)
        logging.info("Action: %s", action)
        logging.info("User comment: %s", user_comment)

        # First user login and process
        login_to_firco(page, url=TEST_URL, username=USERNAME, password=PASSWORD)

        firco_result_user1 = None

        if action != "STP-Release":
            # For non-STP actions, we expect escalation
            logging.info("Processing non-STP action with escalation.")
            firco_result_user1 = process_firco_transaction(
                page,
                transaction,
                action,
                user_comment,
                transaction_type=transaction_type,
                needs_escalation=True,
                perform_on_latest=perform_on_latest,
            )
        else:
            # For STP-Release, process directly without escalation flag initially
            logging.info("Processing STP-Release transaction directly.")
            firco_result_user1 = process_firco_transaction(
                page,
                transaction,
                action,
                user_comment,
                transaction_type=transaction_type,
                perform_on_latest=perform_on_latest,
            )

        # Determine if manager processing is needed based on the result from the
        # first user's session
        needs_manager = firco_result_user1.get("status") == "escalated"

        # If escalation was performed (or if status indicates manager is needed),
        # do manager processing
        if needs_manager:
            logging.info(
                "Manager processing required for transaction %s due to status: %s",
                transaction,
                firco_result_user1.get("status"),
            )
            login_to_firco(
                page, url=TEST_URL, username=MANAGER_USERNAME, password=MANAGER_PASSWORD
            )
            # The action for the manager might be different or implicit post-escalation
            # Assuming the 'action' here is what the manager should perform
            firco_result_manager = process_firco_transaction(
                page,
                transaction,
                action,
                user_comment,
                transaction_type=transaction_type,
            )
            # The final result for the API will be based on the manager's action outcome
            final_firco_result = firco_result_manager
        else:
            # If no manager action was needed, the result from the first user is the final one
            final_firco_result = firco_result_user1

        final_status = final_firco_result.get("status")
        if final_status in SUCCESSFUL_AUTOMATION_STEP_STATUSES:
            result["success"] = True
            result["message"] = final_firco_result.get(
                "message",
                f"Transaction {transaction} status: {final_firco_result.get('status')}",
            )
            result["status_detail"] = final_firco_result.get(
                "status"
            )  # Pass the detailed status
        else:
            # Handle cases where final_firco_result indicates a processing
            # failure or an unexpected status
            result["success"] = False
            result["message"] = final_firco_result.get(
                "message",
                f"Transaction {transaction} failed or has an unknown status: "
                f"{final_firco_result.get('status')}",
            )
            result["error_code"] = final_firco_result.get(
                "error_code", 500
            )  # Default error code
            result["screenshot_path"] = final_firco_result.get("screenshot_path")
            result["status_detail"] = final_firco_result.get(
                "status", "processing_error"
            )  # Pass detailed error status

        # File operations and logging remain largely the same,
        # assuming success means the workflow step completed
        if result["success"]:
            try:
                # Move screenshots into the per-transaction folder
                move_screenshots_to_folder(transaction_folder)
            except FileNotFoundError:
                logging.error("Screenshot folder not found: %s", transaction_folder)
            except PermissionError:
                logging.error(
                    "Permission denied when moving screenshots to %s",
                    transaction_folder,
                )
            except OSError as e:
                logging.error("OS error when moving screenshots: %s", e)

            try:
                os.rename(
                    txt_path,
                    os.path.join(transaction_folder, os.path.basename(txt_path)),
                )
            except FileNotFoundError:
                logging.error("Transaction file not found: %s", txt_path)
            except PermissionError:
                logging.error(
                    "Permission denied when moving transaction file to %s",
                    transaction_folder,
                )
            except FileExistsError:
                logging.error(
                    "A file with the same name already exists in %s", transaction_folder
                )
            except OSError as e:
                logging.error("OS error when moving transaction file: %s", e)

            log_msg = (
                f"Transaction {transaction} processing attempt. "
                f"Final status: {final_firco_result.get('status')}, "
                f"Action: {action}, User: {user_comment}"
            )
            with open(
                os.path.join(OUTPUT_DIR, "daily_log.txt"), "a", encoding="utf-8"
            ) as log:
                log.write(log_msg + "\n")
            logging.info("%s", log_msg)

    except TransactionError as te:
        handle_transaction_error(transaction, action, te, result)
    except (OSError, ConnectionError, ValueError, RuntimeError) as e:
        # Using more specific error types instead of general Exception
        handle_generic_error(transaction, e, result)
    finally:
        cleanup_browser_resources(page, context)

    # Return the result as JSON string for the server to use
    return json.dumps(result)


# --- Main Execution ---
def main() -> None:
    """Main function to set up logging and process all transactions in the input directory."""
    setup_logging()
    logging.info("Script started")

    with sync_playwright() as p:
        for txt_file in get_txt_files(INCOMING_DIR):
            txt_path = os.path.join(INCOMING_DIR, txt_file)
            result = process_transaction(p, txt_path)
            print(result)


if __name__ == "__main__":
    main()
