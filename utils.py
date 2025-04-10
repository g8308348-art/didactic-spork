import os
import logging
from datetime import datetime

# --- Helper Functions ---
def parse_txt_file(txt_path):
    """Parse transaction file to extract transaction, action, and user comment."""
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    
    transaction = lines[0].strip() if len(lines) > 0 else ""
    action = lines[1].strip() if len(lines) > 1 else "STP-Release"
    user_comment = lines[2].strip() if len(lines) > 2 else ""
    
    return transaction, action, user_comment

def create_output_structure(transaction, output_dir):
    """Create output folder structure for transaction."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(output_dir, today)
    transaction_folder = os.path.join(date_folder, transaction)
    
    os.makedirs(date_folder, exist_ok=True)
    os.makedirs(transaction_folder, exist_ok=True)
    
    return transaction_folder, date_folder

def move_screenshots_to_folder(target_folder):
    """Move screenshots from current directory to target folder."""
    for file in os.listdir('.'):
        if file.endswith('.png'):
            try:
                os.rename(file, os.path.join(target_folder, file))
            except Exception as e:
                logging.error(f"Failed to move screenshot {file}: {e}")

def get_txt_files(directory):
    """Get all txt files in a directory."""
    return [f for f in os.listdir(directory) if f.endswith('.txt')]