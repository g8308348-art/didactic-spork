from .logging_setup import setup_logging
from .file_utils import get_txt_files, parse_txt_file, create_output_structure, move_screenshots_to_folder, create_transaction_file
from .browser_utils import login_to_firco
from .firco_actions import process_firco_transaction
from .firco_page import FircoPage
from playwright.sync_api import sync_playwright
import logging, os
import json
from datetime import datetime

def process_transaction(transaction_data, use_browser=False):
    """
    Process a transaction with or without browser automation
    
    Args:
        transaction_data (dict): Dictionary containing transaction details
        use_browser (bool): Whether to use browser automation
        
    Returns:
        dict: Result of the transaction processing
    """
    setup_logging()
    
    # Extract data from the input
    transaction = transaction_data.get('transactions', [])[0] if transaction_data.get('transactions') else ""
    action = transaction_data.get('action', "")
    user_comment = transaction_data.get('comment', "")
    
    if not transaction or not action:
        return {
            'success': False,
            'message': 'Missing transaction ID or action',
            'timestamp': datetime.now().isoformat(),
            'errorCode': 400
        }
    
    # Create transaction file
    try:
        txt_path = create_transaction_file(transaction, action, user_comment)
        logging.info(f"Created transaction file: {txt_path}")
    except Exception as e:
        logging.error(f"Failed to create transaction file: {e}")
        return {
            'success': False,
            'message': f'Failed to create transaction file: {str(e)}',
            'timestamp': datetime.now().isoformat(),
            'errorCode': 500
        }
    
    # If not using browser automation, just simulate processing
    if not use_browser:
        # Simulate success/failure based on transaction ID
        # For testing: transactions starting with 'ERR' will fail
        if transaction.startswith('ERR'):
            return {
                'success': False,
                'message': 'Transaction validation failed',
                'timestamp': datetime.now().isoformat(),
                'errorCode': 422,
                'transaction': transaction,
                'action': action
            }
        
        # Generate a transaction ID
        transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            'success': True,
            'message': f'Transaction processed successfully',
            'timestamp': datetime.now().isoformat(),
            'transactionId': transaction_id,
            'transaction': transaction,
            'action': action
        }
    
    # Use browser automation for real processing
    try:
        with sync_playwright() as playwright:
            transaction_folder, date_folder = create_output_structure(transaction)
            
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                login_to_firco(page)
                firco_page = FircoPage(page)
                success = process_firco_transaction(firco_page, transaction, action, user_comment)
                
                try:
                    move_screenshots_to_folder(date_folder)
                except Exception as e:
                    logging.error(f"Failed to move screenshots: {e}")

                try:
                    os.rename(txt_path, os.path.join(transaction_folder, os.path.basename(txt_path)))
                except Exception as e:
                    logging.error(f"Failed to move transaction file: {e}")

                if success:
                    transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    logging.info(f"Processed transaction: {transaction}, action: {action}, user: {user_comment}")
                    return {
                        'success': True,
                        'message': f'Transaction processed successfully',
                        'timestamp': datetime.now().isoformat(),
                        'transactionId': transaction_id,
                        'transaction': transaction,
                        'action': action
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to process transaction in Firco system',
                        'timestamp': datetime.now().isoformat(),
                        'errorCode': 500,
                        'transaction': transaction,
                        'action': action
                    }
            except Exception as e:
                logging.error(f"Failed processing {transaction}: {e}")
                return {
                    'success': False,
                    'message': f'Error during processing: {str(e)}',
                    'timestamp': datetime.now().isoformat(),
                    'errorCode': 500,
                    'transaction': transaction,
                    'action': action
                }
            finally:
                browser.close()
    except Exception as e:
        logging.error(f"Failed to initialize browser: {e}")
        return {
            'success': False,
            'message': f'Failed to initialize browser: {str(e)}',
            'timestamp': datetime.now().isoformat(),
            'errorCode': 500,
            'transaction': transaction,
            'action': action
        }


def main():
    """Main function for standalone execution"""
    setup_logging()
    logging.info("Script started")
    
    with sync_playwright() as p:
        for txt_file in get_txt_files("input"):
            txt_path = os.path.join("input", txt_file)
            process_transaction_with_playwright(p, txt_path)
            
    logging.info("Script completed")


if __name__ == '__main__':
    main()