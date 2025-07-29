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
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS  # third-party
from playwright.sync_api import sync_playwright  # third-party

from main_logic import INCOMING_DIR, process_transaction  # first-party
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
    root_logger.setLevel(logging.INFO)

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

    # Write temp file and process via existing logic
    temp_path = _write_temp_transaction_file(data)

    try:
        with sync_playwright() as p:
            response_dict = json.loads(
                process_transaction(
                    playwright=p,
                    txt_path=temp_path,
                    transaction_type=transaction_type,
                    perform_on_latest=perform_on_latest,
                )
            )

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
    finally:
        # Clean up temp file
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return jsonify(response_dict), status_code


@app.route("/")
def serve_index():
    """Alias route for root—serves index.html."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/tests-automation")
def serve_tests_automation():
    """Serve the tests-automation HTML page."""
    return send_from_directory(app.static_folder, "tests-automation.html")


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
