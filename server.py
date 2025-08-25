from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import signal
import sys
import logging
import tempfile
from datetime import datetime
from playwright.sync_api import sync_playwright
from filelock import FileLock

# Add the parent directory to sys.path to allow importing from helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Directories (set from env or fall back to defaults) so helpers can be reused
INCOMING_DIR = os.getenv("INCOMING_DIR", "input")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")


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

    # Ensure directories are created atomically to avoid race conditions in multi-threaded mode
    lock_path = os.path.join(OUTPUT_DIR, ".dir.lock")
    with FileLock(lock_path):
        os.makedirs(date_folder, exist_ok=True)
        os.makedirs(transaction_folder, exist_ok=True)

    return transaction_folder, date_folder


def move_screenshots_to_folder(target_folder):
    """Move screenshots from current directory to target folder.
    If destination file already exists, it will be overwritten.
    The original screenshots are removed from the main folder.
    """
    import shutil

    for file in os.listdir("."):
        if file.endswith(".png") and (
            "screenshot" in file
            or "hld" in file
            or "release" in file
            or "transaction" in file
        ):
            src_path = os.path.join(".", file)
            dest_path = os.path.join(target_folder, file)

            try:
                # If destination exists, remove it first to avoid errors
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                    logging.info(f"Removed existing file at destination: {dest_path}")

                # Copy the file to destination
                shutil.copy2(src_path, dest_path)
                logging.info(f"Copied screenshot to: {dest_path}")

                # Remove the original file
                os.remove(src_path)
                logging.info(f"Removed original screenshot: {src_path}")

            except Exception as e:
                logging.error(f"Failed to handle screenshot {file}: {e}")
                # Continue with next file even if this one failed


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

        # Build the file path relative to the 'public' folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "public", self.path.lstrip("/"))
        try:
            with open(file_path, "rb") as file:
                self.send_response(200)
                if self.path.endswith(".html"):
                    self.send_header("Content-type", "text/html")
                elif self.path.endswith(".js"):
                    self.send_header("Content-type", "application/javascript")
                elif self.path.endswith(".css"):
                    self.send_header("Content-type", "text/css")
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

            # Accept transactionType if present
            required_fields = ["transaction", "action", "comment"]
            transaction_type = data.get("transaction_type", "")
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

            logging.info(f"Received transactionType: {transaction_type}")
            # Create a temporary file with the transaction data
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", delete=False, dir=INCOMING_DIR, suffix=".txt"
                ) as temp_file:
                    temp_file_path = temp_file.name
                    # Format the data as expected by parse_txt_file
                    temp_file.write(
                        f"{data['transaction']}\n{data['action']}\n{data['comment']}\n{transaction_type}"
                    )

                logging.info(f"Created temporary file: {temp_file_path}")

                perform_on_latest = bool(data.get("performOnLatest", False))

                with sync_playwright() as playwright:
                    response = process_transaction(
                        playwright,
                        temp_file_path,
                        transaction_type=transaction_type,
                        perform_on_latest=perform_on_latest,
                    )
                    # Ensure response is a dict, not a JSON string
                    if isinstance(response, str):
                        response = json.loads(response)

                # Check if processing was successful
                if response["success"]:
                    response = {
                        "success": True,
                        "message": response["message"],
                        "status_detail": response.get(
                            "status_detail", response.get("status")
                        ),  # Include status_detail for frontend
                        "transactionId": os.path.basename(temp_file_path).split(".")[0],
                    }
                else:
                    # Include detailed error information
                    response = {
                        "success": False,
                        "message": response["message"],
                        "errorCode": response["error_code"],
                        "screenshotPath": response["screenshot_path"],
                        "status_detail": response.get(
                            "status_detail", response.get("status")
                        ),  # Include status_detail for frontend
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


def run(
    server_class=ThreadingHTTPServer,
    handler_class=SimpleHTTPRequestHandler,
    host: str = "0.0.0.0",
    port: int = 8088,
):
    # Set up logging
    setup_logging()
    logging.info("Starting server on %s:%s ...", host, port)

    # Ensure directories exist
    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    server_address = (host, port)
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
    run()  # uses default host 0.0.0.0 and port 8088
