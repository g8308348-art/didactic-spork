# pylint: disable=import-error,import-outside-toplevel,broad-except
"""Flask-based replacement of the legacy http.server implementation.

Provides the same /api endpoint but benefits from Flask's routing and
thread-friendliness. Keep the file largely self-contained while
re-using helper utilities that already exist in *server/server.py* and
*main_logic.py* so we avoid code duplication.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import sys
import time
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS  # third-party
from playwright.sync_api import sync_playwright  # third-party

from firco.firco_page import FircoPage  # first-party
from server import create_output_structure, move_screenshots_to_folder  # first-party

# Create Flask application
app = Flask(__name__, static_folder="public")
# Enable CORS for all routes (development convenience)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------


def setup_logging():
    """Configure logging to output to both console and transactions.log file."""
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (10 MB max size, keep 5 backup files)
    file_handler = RotatingFileHandler(
        "transactions.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured to console and transactions.log file")


# ---------------------------------------------------------------------------
# Helper utilities specific to this Flask layer
# ---------------------------------------------------------------------------


def _write_temp_transaction_file(data: Dict[str, str]) -> str:
    """Write incoming JSON to a temp TXT file mimicking original flow.

    Returns the path to the created file so the caller can pass it to
    *process_transaction* and later clean it up.
    """
    os.makedirs(INCOMING_DIR, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=INCOMING_DIR, suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        # line-per-line format expected by parse_txt_file
        f.write(f"{data['transaction']}\n")
        f.write(f"{data.get('action', 'STP-Release')}\n")
        f.write(f"{data.get('comment', '')}\n")
    return temp_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/logs")
def serve_logs():
    """Return the contents of `transactions.log` as plain text.

    The endpoint is intentionally simple for internal troubleshooting
    purposes. If the log file grows large we stream it line-by-line to
    avoid loading the entire file into memory at once.
    """

    def generate() -> str:  # pragma: no cover
        try:
            with open(
                "transactions.log", "r", encoding="utf-8", errors="replace"
            ) as log_file:
                for line in log_file:
                    yield line
        except FileNotFoundError:
            yield "transactions.log not found."

    return app.response_class(generate(), mimetype="text/plain")


# Serve next_steps.md as Markdown (rendered as text/markdown)
@app.route("/next_steps")
def serve_next_steps():
    """Stream `next_steps.md` so encoding glitches won't crash the endpoint."""
    md_path = os.path.join(os.path.dirname(__file__), "next_steps.md")
    if not os.path.isfile(md_path):
        return make_response("next_steps.md not found", 404)

    def generate() -> str:  # pragma: no cover
        with open(md_path, "r", encoding="utf-8", errors="replace") as md_file:
            for line in md_file:
                yield line

    return app.response_class(generate(), mimetype="text/markdown")


@app.after_request
def add_cors_headers(resp):
    """Inject CORS headers on every response (dev convenience)."""
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return resp


# Serve the SPA
@app.route("/")
def index():
    """Serve the single-page application entry HTML."""
    return send_from_directory(app.static_folder, "index.html")


# Fallback for any other static assets (CSS, JS, images)
@app.route("/<path:path>")
def static_proxy(path):
    """Serve other static assets (CSS, JS, images)."""
    return send_from_directory(app.static_folder, path)


@app.route("/api/generate-test-files", methods=["POST", "OPTIONS"])
def generate_test_files():
    """Generate XML test files based on a template.

    Expected JSON: {testName: str, placeholders: {key: value}}
    Returns JSON {success, files: [relative paths]}
    Currently forwards to *tests_automation* helper when available.
    """
    if request.method == "OPTIONS":
        # Pre-flight CORS request
        return make_response("", 200)

    try:
        data = request.get_json(force=True)
    except Exception:  # pylint: disable=broad-except
        return jsonify(success=False, error="Invalid JSON"), 400

    test_name = data.get("testName")
    if not test_name:
        return jsonify(success=False, error="testName is required"), 400

    try:
        from tests_automation.xml_processor import (
            XMLTemplateProcessor,  # type: ignore # pylint: disable=import-error,import-outside-toplevel
        )

        template_file = os.path.join(
            os.path.dirname(__file__),
            "tests-automation",
            "templates",
            "PCC_TAIWAN_ISO.xml",
        )
        processor = XMLTemplateProcessor(template_path=template_file)
        placeholders = data.get("placeholders", {}) or {}
        files = processor.generate_test_files(
            "Cuban Filter", extra_placeholders=placeholders
        )
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Failed to generate XML files")
        return jsonify(success=False, error=str(exc)), 500

    if not files:
        return jsonify(success=False, error="No files were generated"), 400

    # Return relative paths for front-end to link
    rel_files = [os.path.relpath(f, start=app.static_folder) for f in files]
    return (
        jsonify(
            success=True,
            files=rel_files,
            outputDir=os.path.relpath(
                os.path.dirname(files[0]), start=app.static_folder
            ),
        ),
        200,
    )


@app.route("/api", methods=["POST"])
def process_api() -> Any:  # noqa: D401
    """Main automation endpoint consumed by the SPA.

    Expects JSON {transaction, action, comment, transactionType?, performOnLatest?}
    """
    try:
        data = request.get_json(force=True)  # will raise on invalid JSON
    except json.JSONDecodeError:
        return jsonify(success=False, message="Invalid JSON"), 400

    required = {"transaction", "action", "comment"}
    if not required.issubset(data):
        return (
            jsonify(
                success=False,
                message=f"Missing required fields: {required - data.keys()}",
            ),
            400,
        )

    # Optional fields
    transaction_type = data.get("transactionType", "")
    perform_on_latest = bool(data.get("performOnLatest", False))

    try:
        # Run Playwright and use FircoPage directly
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                firco = FircoPage(page)
                response_dict = firco.flow_start(
                    data["transaction"],
                    data["action"],
                    data["comment"],
                    transaction_type,
                )
            finally:
                # Ensure resources are closed
                try:
                    context.close()
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass

        # Move screenshots if successful (or containing hits)
        transaction_folder, _ = create_output_structure(data["transaction"])
        try:
            move_screenshots_to_folder(transaction_folder)
        except Exception as move_err:
            logging.warning("Failed moving screenshots: %s", move_err)

        status_code = 200
    except Exception as err:  # pylint: disable=broad-except
        logging.exception("Error processing transaction: %s", err)
        response_dict = {"success": False, "message": str(err)}
        status_code = 500

    return jsonify(response_dict), status_code


@app.route("/")
def serve_index():
    """Alias route for root—serves index.html."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/tests-automation")
def serve_tests_automation():
    """Serve the tests-automation HTML page."""
    return send_from_directory(app.static_folder, "tests-automation.html")


@app.route("/bpm")
def serve_bpm():
    """Serve the BPM transaction search HTML page."""
    return send_from_directory(app.static_folder, "bpm.html")


@app.route("/api/bpm", methods=["POST", "OPTIONS"])
def process_bpm_search():
    """Handle BPM search requests with comprehensive error handling.

    Expected JSON: {transactionId: str, marketType: str}
    Returns JSON response with search results or detailed error information.
    """
    if request.method == "OPTIONS":
        # Pre-flight CORS request
        return make_response("", 200)

    # Enhanced request logging for debugging
    request_id = f"req_{hash(str(request.data) + str(request.headers))}"
    logging.info(
        "BPM search request started - ID: %s, IP: %s", request_id, request.remote_addr
    )

    try:
        data = request.get_json(force=True)
        logging.debug("Request data received - ID: %s, Data: %s", request_id, data)
    except json.JSONDecodeError as e:
        logging.warning("Invalid JSON received - ID: %s, Error: %s", request_id, e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid JSON in request body. Please check your request format.",
                    "errorCode": "INVALID_JSON",
                    "requestId": request_id,
                }
            ),
            400,
        )
    except Exception as e:
        logging.error(
            "Unexpected error parsing request - ID: %s, Error: %s", request_id, e
        )
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to process request body",
                    "errorCode": "REQUEST_PROCESSING_ERROR",
                    "requestId": request_id,
                }
            ),
            400,
        )

    # Validate request body exists
    if not data:
        logging.warning("Empty request body received - ID: %s", request_id)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Request body is required. Please provide transactionId and marketType.",
                    "errorCode": "MISSING_REQUEST_BODY",
                    "requestId": request_id,
                }
            ),
            400,
        )

    # Extract and sanitize input data
    transaction_id = data.get("transactionId", "").strip()
    market_type = data.get("marketType", "").strip()

    # Enhanced input validation with detailed error messages
    validation_errors = []

    if not transaction_id:
        validation_errors.append("Transaction ID is required")
        logging.warning("Missing transaction ID - ID: %s", request_id)
    elif len(transaction_id) < 3:
        validation_errors.append("Transaction ID must be at least 3 characters long")
        logging.warning(
            "Transaction ID too short - ID: %s, Length: %d",
            request_id,
            len(transaction_id),
        )
    elif len(transaction_id) > 50:
        validation_errors.append(
            "Transaction ID must be no more than 50 characters long"
        )
        logging.warning(
            "Transaction ID too long - ID: %s, Length: %d",
            request_id,
            len(transaction_id),
        )

    if not market_type:
        validation_errors.append("Market type is required")
        logging.warning("Missing market type - ID: %s", request_id)

    # Return validation errors if any
    if validation_errors:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "; ".join(validation_errors),
                    "errorCode": "VALIDATION_ERROR",
                    "validationErrors": validation_errors,
                    "requestId": request_id,
                }
            ),
            400,
        )

    # Validate market type against available options
    try:
        from bpm.bpm_page import Options

        valid_market_types = [opt.name for opt in Options] + [
            opt.value for opt in Options
        ]
        if market_type not in valid_market_types:
            logging.warning(
                "Invalid market type - ID: %s, Type: %s", request_id, market_type
            )
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Invalid market type '{market_type}'. Valid options are: {', '.join([opt.value for opt in Options])}",
                        "errorCode": "INVALID_MARKET_TYPE",
                        "validOptions": [opt.value for opt in Options],
                        "requestId": request_id,
                    }
                ),
                400,
            )
    except ImportError as e:
        logging.error("Failed to import BPM Options - ID: %s, Error: %s", request_id, e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "BPM system configuration is not available. Please contact system administrator.",
                    "errorCode": "SYSTEM_CONFIGURATION_ERROR",
                    "requestId": request_id,
                }
            ),
            500,
        )
    except Exception as e:
        logging.error(
            "Unexpected error validating market type - ID: %s, Error: %s", request_id, e
        )
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "System error during validation. Please try again later.",
                    "errorCode": "VALIDATION_SYSTEM_ERROR",
                    "requestId": request_id,
                }
            ),
            500,
        )

    # Enhanced input sanitization with detailed validation
    import re

    if not re.match(r"^[a-zA-Z0-9_-]+$", transaction_id):
        logging.warning(
            "Invalid transaction ID format - ID: %s, TransactionID: %s",
            request_id,
            transaction_id,
        )
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Transaction ID contains invalid characters. Only alphanumeric characters, hyphens, and underscores are allowed.",
                    "errorCode": "INVALID_TRANSACTION_ID_FORMAT",
                    "allowedCharacters": "Letters (a-z, A-Z), numbers (0-9), hyphens (-), and underscores (_)",
                    "requestId": request_id,
                }
            ),
            400,
        )

    # Call BPM automation with comprehensive error handling
    start_time = time.time()
    try:
        from bpm.bpm import main as bpm_main
        from bpm.bpm_page import map_transaction_type_to_option, Options

        logging.info(
            "Starting BPM automation - ID: %s, Transaction: %s, Market: %s",
            request_id,
            transaction_id,
            market_type,
        )

        # Map frontend market type to Options enum
        mapped_options = map_transaction_type_to_option(market_type)
        if not mapped_options:
            logging.warning(
                "Failed to map market type - ID: %s, Type: %s", request_id, market_type
            )
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Unable to process market type '{market_type}'. Valid options are: {', '.join([opt.value for opt in Options])}",
                        "errorCode": "MARKET_TYPE_MAPPING_ERROR",
                        "validOptions": [opt.value for opt in Options],
                        "requestId": request_id,
                    }
                ),
                400,
            )

        # Call the BPM main function with timeout handling
        try:
            bpm_result = bpm_main(market_type, transaction_id)
            execution_time = round(
                (time.time() - start_time) * 1000, 2
            )  # Convert to milliseconds

            logging.info(
                "BPM automation completed - ID: %s, Duration: %sms",
                request_id,
                execution_time,
            )

        except TimeoutError as e:
            logging.error("BPM automation timeout - ID: %s, Error: %s", request_id, e)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "BPM search timed out. The system may be busy, please try again later.",
                        "errorCode": "BPM_TIMEOUT_ERROR",
                        "requestId": request_id,
                    }
                ),
                504,
            )

        # Handle specific BPM result statuses
        if bpm_result and bpm_result.get("status") == "transaction_type_not_defined":
            logging.warning("Transaction type not defined - ID: %s", request_id)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Transaction type was not defined in the system. BPM search was skipped.",
                        "errorCode": "TRANSACTION_TYPE_NOT_DEFINED",
                        "requestId": request_id,
                    }
                ),
                400,
            )

        # Format successful response with enhanced metadata
        response_data = {
            "status": "ok",
            "results": {
                "transactionId": transaction_id,
                "marketType": market_type,
                "searchCompleted": True,
                "bpmResult": bpm_result or {"status": "completed"},
                "mappedOptions": (
                    [opt.value for opt in mapped_options] if mapped_options else []
                ),
                "executionTime": execution_time,
                "requestId": request_id,
            },
        }

        # Add timestamp
        import datetime

        response_data["results"]["searchTime"] = datetime.datetime.now().isoformat()

        logging.info(
            "BPM search successful - ID: %s, Transaction: %s",
            request_id,
            transaction_id,
        )
        return jsonify(response_data), 200

    except ImportError as e:
        logging.error("BPM module import failed - ID: %s, Error: %s", request_id, e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "BPM automation system is not available. Please ensure the system is properly configured.",
                    "errorCode": "BPM_SYSTEM_UNAVAILABLE",
                    "technicalDetails": "Required BPM modules could not be loaded",
                    "requestId": request_id,
                }
            ),
            503,
        )
    except PermissionError as e:
        logging.error("BPM permission error - ID: %s, Error: %s", request_id, e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Insufficient permissions to access BPM system. Please contact system administrator.",
                    "errorCode": "BPM_PERMISSION_ERROR",
                    "requestId": request_id,
                }
            ),
            403,
        )
    except ConnectionError as e:
        logging.error("BPM connection error - ID: %s, Error: %s", request_id, e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Unable to connect to BPM system. Please check network connectivity and try again.",
                    "errorCode": "BPM_CONNECTION_ERROR",
                    "requestId": request_id,
                }
            ),
            503,
        )
    except ValueError as e:
        logging.error("BPM value error - ID: %s, Error: %s", request_id, e)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Invalid data provided to BPM system: {str(e)}",
                    "errorCode": "BPM_DATA_ERROR",
                    "requestId": request_id,
                }
            ),
            400,
        )
    except Exception as e:
        execution_time = round((time.time() - start_time) * 1000, 2)
        logging.error(
            "BPM automation unexpected error - ID: %s, Duration: %sms, Error: %s",
            request_id,
            execution_time,
            e,
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An unexpected error occurred during BPM search. Please try again or contact support if the problem persists.",
                    "errorCode": "BPM_AUTOMATION_ERROR",
                    "technicalDetails": (
                        str(e) if app.debug else "Contact support for technical details"
                    ),
                    "requestId": request_id,
                }
            ),
            500,
        )


# Flask already serves static files when `static_folder` is configured.

# ---------------------------------------------------------------------------
# Application entry-point
# ---------------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    """Run the Flask app with thread support (development use)."""
    setup_logging()
    logging.info("Starting Flask server on http://0.0.0.0:8088 …")
    app.run(host="0.0.0.0", port=8088, threaded=True)


if __name__ == "__main__":
    main()
