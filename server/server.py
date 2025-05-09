from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import signal
import sys
import logging
import tempfile
from datetime import datetime
from utils import parse_txt_file, create_output_structure, move_screenshots_to_folder


# Add the parent directory to sys.path to allow importing from helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from main_logic.py
from main_logic import process_transaction, setup_logging, INCOMING_DIR, OUTPUT_DIR


# Helper functions that are missing in main_logic.py
def parse_txt_file(txt_path):
    """Parse transaction file to extract transaction, action, and user comment."""
    with open(txt_path, "r") as f:
        lines = f.readlines()

    transaction = lines[0].strip() if len(lines) > 0 else ""
    action = lines[1].strip() if len(lines) > 1 else "STP-Release"
    user_comment = lines[2].strip() if len(lines) > 2 else ""

    return transaction, action, user_comment


def create_output_structure(transaction):
    """Create output folder structure for transaction."""
    today = datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(OUTPUT_DIR, today)
    transaction_folder = os.path.join(date_folder, transaction)

    os.makedirs(date_folder, exist_ok=True)
    os.makedirs(transaction_folder, exist_ok=True)

    return transaction_folder, date_folder


def move_screenshots_to_folder(target_folder):
    """Move screenshots from current directory to target folder."""
    for file in os.listdir("."):
        if file.endswith(".png") and "screenshot" in file:
            try:
                os.rename(file, os.path.join(target_folder, file))
            except Exception as e:
                logging.error("Failed to move screenshot %s: %s", file, e)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set headers for CORS support"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        # Serve index.html for the root endpoint
        if self.path == "/":
            self.path = "/index.html"

        # Build the file path relative to the 'static' folder
        file_path = os.path.join(os.getcwd(), "static", self.path.lstrip("/"))
        try:
            with open(file_path, "rb") as file:
                self.send_response(200)
                if self.path.endswith(".html"):
                    self.send_header("Content-type", "text/html")
                elif self.path.endswith(".js"):
                    self.send_header("Content-type", "application/javascript")
                else:
                    self.send_header("Content-type", "application/octet-stream")
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(404, "File not found: " + self.path)

    def do_POST(self):
        # Define a simple API endpoint at /api
        if self.path == "/api":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b"Invalid JSON")
                return

            # Ensure required fields are present
            required_fields = ["transaction", "action", "comment"]
            if not all(key in data for key in required_fields):
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(
                    f'Missing required fields: {", ".join(required_fields)}'.encode(
                        "utf-8"
                    )
                )
                return

            # Create a temporary file with the transaction data
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", delete=False, dir=INCOMING_DIR, suffix=".txt"
                ) as temp_file:
                    temp_file_path = temp_file.name
                    # Format the data as expected by parse_txt_file
                    temp_file.write(
                        f"{data['transaction']}\n{data['action']}\n{data['comment']}"
                    )

                logging.info(f"Created temporary file: {temp_file_path}")

                # Process the transaction using our main logic
                from playwright.sync_api import sync_playwright

                perform_on_latest = bool(data.get('performOnLatest', False))
                from main_logic import process_transaction
                from playwright.sync_api import sync_playwright

                with sync_playwright() as playwright:
                    result_json = process_transaction(playwright, temp_file_path)
                    result = json.loads(result_json)

                # Check if processing was successful
                if result["success"]:
                    response = {
                        "success": True,
                        "message": result["message"],
                        "transactionId": os.path.basename(temp_file_path).split(".")[0],
                    }
                else:
                    # Include detailed error information
                    response = {
                        "success": False,
                        "message": result["message"],
                        "errorCode": result["error_code"],
                        "screenshotPath": result["screenshot_path"],
                    }

                    # If temp file was created but processing failed, we should clean it up
                    if os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                            logging.info(
                                f"Cleaned up temporary file after error: {temp_file_path}"
                            )
                        except Exception as cleanup_error:
                            logging.error(
                                f"Failed to clean up temporary file: {cleanup_error}"
                            )

            except Exception as e:
                logging.error(f"Error processing transaction: {str(e)}")
                response = {"success": False, "message": str(e), "errorCode": 500}

                # If temp file was created but processing failed, we should clean it up
                if "temp_file_path" in locals() and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        logging.info(f"Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        logging.error(
                            f"Failed to clean up temporary file: {cleanup_error}"
                        )

            response_data = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", len(response_data))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(response_data)
        else:
            self.send_error(404, "Endpoint not found")


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8080):
    # Set up logging
    setup_logging()
    logging.info("Starting server on port %s...", port)

    # Ensure directories exist
    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    server_address = ("", port)
    httpd = server_class(server_address, handler_class)

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logging.info("Shutting down the server gracefully...")
        httpd.server_close()
        logging.info("Server has been shut down")
        sys.exit(0)

    # Register the signal handler for CTRL+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)

    logging.info("Press CTRL+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        logging.info("Server has been shut down")


if __name__ == "__main__":
    run()
