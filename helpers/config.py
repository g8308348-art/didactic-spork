"""
Configuration settings for the transaction processing system
"""
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create directories if they don't exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging
LOG_FILE = os.path.join(LOG_DIR, f"transactions_{datetime.now().strftime('%Y%m%d')}.log")

# Firco system credentials - these should be loaded from environment variables in production
TEST_URL = os.getenv("TEST_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Processing settings
HEADLESS = False  # Set to True in production
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
