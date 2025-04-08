import os
import shutil
import logging
from datetime import datetime

def get_txt_files(directory):
    """Get all .txt files in the specified directory"""
    return [f for f in os.listdir(directory) if f.endswith('.txt')]

def parse_txt_file(file_path):
    """Parse a transaction file to extract transaction ID, action, and comment"""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Expecting format: transaction in first line, action in second, comment in third
            transaction = lines[0].strip() if len(lines) > 0 else ""
            action = lines[1].strip() if len(lines) > 1 else "STP-Release"
            comment = lines[2].strip() if len(lines) > 2 else ""
            return transaction, action, comment
    except Exception as e:
        logging.error(f"Error parsing file {file_path}: {e}")
        return None, None, None

def create_output_structure(transaction, base_dir="output"):
    """Create directory structure for output files"""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(base_dir, today)
    transaction_folder = os.path.join(date_folder, transaction)
    
    # Create directories if they don't exist
    os.makedirs(date_folder, exist_ok=True)
    os.makedirs(transaction_folder, exist_ok=True)
    
    return transaction_folder, date_folder

def move_screenshots_to_folder(target_folder):
    """Move any screenshots to the specified folder"""
    downloads_dir = os.path.expanduser("~/Downloads")
    for file in os.listdir(downloads_dir):
        if file.startswith("screenshot") and (file.endswith(".png") or file.endswith(".jpg")):
            source = os.path.join(downloads_dir, file)
            destination = os.path.join(target_folder, file)
            shutil.move(source, destination)
            logging.info(f"Moved screenshot {file} to {target_folder}")

def create_transaction_file(transaction, action, comment, directory="input"):
    """Create a transaction file for processing"""
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{transaction}_{timestamp}.txt"
    file_path = os.path.join(directory, filename)
    
    with open(file_path, 'w') as file:
        file.write(f"{transaction}\n{action}\n{comment}")
    
    return file_path