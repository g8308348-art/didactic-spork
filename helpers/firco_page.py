"""
FircoPage class for interacting with the Firco transaction system
"""
from playwright.sync_api import Page
import logging
import time

class FircoPage:
    def __init__(self, page: Page):
        self.page = page
        # Define selectors for important elements
        self.searchInput = page.locator("#transaction-search")
        self.searchButton = page.locator("button.search-btn")
        self.commentInput = page.locator("#transaction-comment")
        self.releaseBtn = page.locator("button.release-btn")
        self.stpReleaseBtn = page.locator("button.stp-release-btn")
        self.blockBtn = page.locator("button.block-btn")
        self.rejectBtn = page.locator("button.reject-btn")
        self.escalateBtn = page.locator("button.escalate-btn")
        self.logoutBtn = page.locator("button.logout-btn")
    
    def go_to_transaction_details(self, transaction_id, comment=None):
        """Navigate to transaction details page"""
        try:
            # Search for the transaction
            self.searchInput.fill(transaction_id)
            self.searchButton.click()
            
            # Wait for results and click on the transaction
            self.page.wait_for_selector(f"text={transaction_id}")
            self.page.click(f"text={transaction_id}")
            
            # Wait for transaction details to load
            self.page.wait_for_selector(".transaction-details")
            
            # Add comment if provided
            if comment and comment.strip():
                self.commentInput.fill(comment)
            
            logging.info(f"Navigated to transaction details for {transaction_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to navigate to transaction {transaction_id}: {e}")
            # Take screenshot of the error
            self.page.screenshot(path=f"screenshot_error_{transaction_id}.png")
            return False
    
    def perform_action(self, action):
        """Perform the specified action on the transaction"""
        try:
            if action == "STP-Release":
                self.stpReleaseBtn.click()
            elif action == "Release":
                self.releaseBtn.click()
            elif action == "Block":
                self.blockBtn.click()
            elif action == "Reject":
                self.rejectBtn.click()
            else:
                logging.warning(f"Unknown action: {action}")
                return False
            
            # Wait for confirmation dialog and confirm
            self.page.wait_for_selector(".confirmation-dialog")
            self.page.click("button.confirm-btn")
            
            # Wait for success message
            self.page.wait_for_selector(".success-message")
            
            # Take a screenshot of the result
            self.page.screenshot(path=f"screenshot_success_{action}.png")
            
            logging.info(f"Successfully performed action: {action}")
            return True
        except Exception as e:
            logging.error(f"Failed to perform action {action}: {e}")
            self.page.screenshot(path=f"screenshot_action_error.png")
            return False
    
    def logout(self):
        """Logout from the system"""
        try:
            self.logoutBtn.click()
            self.page.wait_for_selector(".login-page")
            logging.info("Successfully logged out")
            return True
        except Exception as e:
            logging.error(f"Failed to logout: {e}")
            return False
