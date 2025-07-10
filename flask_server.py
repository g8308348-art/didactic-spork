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
from datetime import datetime
from typing import Any, Dict

from filelock import FileLock
from flask import Flask, jsonify, request, send_from_directory
from main_logic import (
    INCOMING_DIR,
    OUTPUT_DIR,
    process_transaction,
    setup_logging,
)
from server.server import (
    parse_txt_file,
    create_output_structure,
    move_screenshots_to_folder,
)
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Logging configuration (console + file) for Flask process
# ---------------------------------------------------------------------------
from main_logic import setup_logging, LOG_FILE  # reuse helper

root_logger = logging.getLogger()
if not root_logger.handlers:
    # First import / main process – initialise
    setup_logging()
else:
    # When running under Flask's reloader a handler may already exist; ensure file handler present
    if not any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith(LOG_FILE)
        for h in root_logger.handlers
    ):
        root_logger.addHandler(logging.FileHandler(LOG_FILE, encoding="utf-8"))

# Make sure Werkzeug HTTP logs propagate
logging.getLogger("werkzeug").setLevel(logging.INFO)
logging.getLogger("werkzeug").propagate = True

# Serve files from 'public' so index.html is accessible at root
app = Flask(__name__, static_folder="public", static_url_path="")

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

# Serve the SPA
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# Fallback for any other static assets (CSS, JS, images)
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api", methods=["POST"])
def process_api() -> Any:  # noqa: D401
    """Handle an automation request.

    Expects JSON {transaction, action, comment, transactionType?, performOnLatest?}
    """
    try:
        data = request.get_json(force=True)  # will raise on invalid JSON
    except Exception:
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
    except Exception as e:
        logging.exception("Error processing transaction: %s", e)
        response_dict = {"success": False, "message": str(e)}
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
    return send_from_directory(app.static_folder, "index.html")


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
