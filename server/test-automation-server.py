import os
import sys
import json
import http.server
import socketserver
from datetime import datetime
from playwright.sync_api import sync_playwright
from bpm import perform_login_and_setup, select_options_and_submit, handle_dropdown_and_search
from Bpm_Page import BPMPage, Options
from xml_processor import XMLTemplateProcessor
from mtex import main as mtex_main
from disposition_service import run_disposition
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8090
TEMPLATES_DIR = os.path.join(SERVER_DIR, "templates")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")  # Changed to use 'output' folder
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        self.directory = "public"
        super().__init__(*args, directory=self.directory, **kwargs)

    def _set_headers(self, status_code=200, content_type="application/json"):
        """Set common headers including CORS"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS method for CORS preflight"""
        self._set_headers(200)
        self.wfile.write(b"")

    def do_GET(self):
        # Handle API endpoints
        if self.path.startswith("/api/"):
            return self.handle_api_request()

        # Serve static files
        try:
            # Default to index.html if path is root
            if self.path == "/":
                self.path = "/tests-automation.html"

            # Check if file exists
            file_path = os.path.join(PUBLIC_DIR, self.path.lstrip("/"))
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                self.send_error(404, "File not found")
                return

            # Set content type based on file extension
            if file_path.endswith(".html"):
                mimetype = "text/html"
            elif file_path.endswith(".js"):
                mimetype = "application/javascript"
            elif file_path.endswith(".css"):
                mimetype = "text/css"
            else:
                mimetype = "application/octet-stream"

            self._set_headers(200, mimetype)
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())

        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        try:
            if self.path == "/api/generate-test-files":
                return self.handle_generate_test_files()
            elif self.path == "/api/upload-to-mtex":
                return self.handle_upload_to_mtex()
            elif self.path == "/api/disposition-transactions":
                return self.handle_disposition_transactions()
            elif self.path == "/api/generate-pdf":
                return self.handle_generate_pdf()
            self.send_error(404, "Not Found")
        except Exception as e:
            print(f"Error in POST handler: {str(e)}")
            self._set_headers(500)
            self.wfile.write(
                json.dumps(
                    {"success": False, "error": f"Internal server error: {str(e)}"}
                ).encode()
            )

    def handle_api_request(self):
        if self.path == "/api/test-types":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"testTypes": ["Screening response", "Cuban Filter"]}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404, "API endpoint not found")

    def handle_generate_test_files(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
            else:
                data = {}

            test_name = data.get("testName")
            placeholders = data.get("placeholders", {})

            if not test_name:
                self._set_headers(400)
                self.wfile.write(
                    json.dumps(
                        {"success": False, "error": "Test name is required"}
                    ).encode()
                )
                return

            # Process the template
            test_name_lower = test_name.lower().replace(" ", "_")

            # For screening response, we always use the same template
            if test_name == "Screening response":
                template_filename = "screening_response_template.xml"
            else:
                template_filename = f"{test_name_lower}_template.xml"

            template_path = os.path.join(TEMPLATES_DIR, template_filename)
            print(f"[DEBUG] Looking for template: {template_filename}")

            print(f"\n[DEBUG] Looking for template at: {template_path}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            print(f"[DEBUG] Templates directory: {TEMPLATES_DIR}")
            print(
                f"[DEBUG] Files in templates dir: {os.listdir(TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else 'Directory not found'}"
            )

            if not os.path.exists(template_path):
                error_msg = f"Template not found: {template_path} (cwd: {os.getcwd()})"
                print(f"[ERROR] {error_msg}")
                self._set_headers(404)
                self.wfile.write(
                    json.dumps({"success": False, "error": error_msg}).encode()
                )
                return

            print(f"[DEBUG] Found template at: {template_path}")

            # Create output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(OUTPUT_DIR, timestamp)
            os.makedirs(output_dir, exist_ok=True)
            print(f"Output directory: {output_dir}")

            # Process the template
            processor = XMLTemplateProcessor(template_path, output_dir)
            generated_files = processor.generate_test_files(test_name)

            # Convert to relative paths for the frontend
            relative_files = [
                os.path.join("output", timestamp, os.path.basename(f))
                for f in generated_files
            ]
            print(f"Generated files: {generated_files}")
            print(f"Relative files: {relative_files}")

            # Derive UPI from folder timestamp and XML action
            xml_files = [f for f in generated_files if f.lower().endswith(".xml")]
            if xml_files:
                first_basename = os.path.basename(xml_files[0])
                base, _ = os.path.splitext(first_basename)
                action_part = base.split("_")[-1]
                upi_value = timestamp.replace("_", "") + "-" + action_part
            else:
                upi_value = timestamp.replace("_", "")

            # Prepare response
            response = {
                "success": True,
                "files": relative_files,
                "outputDir": timestamp,
                "upi": upi_value,
            }

            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_error(500, f"Error generating test files: {str(e)}")

    def handle_upload_to_mtex(self):
        """Handle MTex upload via mtex.py script"""
        try:
            # Read request body for outputDir override
            length = int(self.headers.get("Content-Length", 0))
            if length:
                post_data = self.rfile.read(length)
                data = json.loads(post_data.decode())
                output_dir_name = data.get("outputDir")
                if not output_dir_name:
                    raise ValueError("Missing outputDir in request")
                test_data_override = os.path.join(OUTPUT_DIR, output_dir_name)
            else:
                test_data_override = None

            mtex_main(test_data_override)
            self._set_headers(200)
            self.wfile.write(
                json.dumps(
                    {"success": True, "message": "Upload to MTex completed"}
                ).encode()
            )
        except Exception as ex:
            self._set_headers(500)
            err = str(ex)
            self.wfile.write(json.dumps({"success": False, "error": err}).encode())

    def handle_disposition_transactions(self):
        """Process transactions and snapshot pages to a screenshots folder"""
        try:
            # Read request body for outputDir and action
            length = int(self.headers.get("Content-Length", 0))
            if length:
                post_data = self.rfile.read(length)
                data = json.loads(post_data.decode())
                output_dir_name = data.get("outputDir")
                action = data.get("action")
                upi = data.get("upi")
                if not output_dir_name or not action or not upi:
                    raise ValueError("Missing outputDir, action, or upi")
            else:
                raise ValueError("Empty request body")

            # Prepare common screenshot folder and BPM pre-check
            date_folder = datetime.now().strftime("%Y-%m-%d")
            screenshot_folder = os.path.join(OUTPUT_DIR, date_folder, upi)
            os.makedirs(screenshot_folder, exist_ok=True)
            with sync_playwright() as pw:
                browser_bpm = pw.chromium.connect_over_cdp("http://localhost:9222")
                ctx_bpm = browser_bpm.new_context()
                page_bpm = ctx_bpm.new_page()
                bpm_page = BPMPage(page_bpm)
                perform_login_and_setup(bpm_page)
                select_options_and_submit(bpm_page, page_bpm, [Options.ENTERPRISE_ISO])
                before_val, _ = handle_dropdown_and_search(bpm_page, page_bpm, upi)
                pre_path = os.path.join(screenshot_folder, f"bpm_before_{upi}.png")
                page_bpm.screenshot(path=pre_path, full_page=True)
                ctx_bpm.close()
                browser_bpm.close()

            # Run disposition and collect MTex screenshots
            result = run_disposition(output_dir_name, action, upi)
            # Ensure result uses our combined folder
            result["screenshot_path"] = screenshot_folder

            # BPM post-check
            with sync_playwright() as pw2:
                browser_bpm2 = pw2.chromium.connect_over_cdp("http://localhost:9222")
                ctx_bpm2 = browser_bpm2.new_context()
                page_bpm2 = ctx_bpm2.new_page()
                bpm_page2 = BPMPage(page_bpm2)
                perform_login_and_setup(bpm_page2)
                select_options_and_submit(bpm_page2, page_bpm2, [Options.ENTERPRISE_ISO])
                after_val, _ = handle_dropdown_and_search(bpm_page2, page_bpm2, upi)
                post_path = os.path.join(screenshot_folder, f"bpm_after_{upi}.png")
                page_bpm2.screenshot(path=post_path, full_page=True)
                ctx_bpm2.close()
                browser_bpm2.close()

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "success": True,
                "screenshotsDir": screenshot_folder,
                "result": result,
                "bpm_before_value": before_val,
                "bpm_after_value": after_val,
            }).encode())
        except Exception as ex:
            self._set_headers(500)
            self.wfile.write(json.dumps({"success": False, "error": str(ex)}).encode())

    def handle_generate_pdf(self):
        """Generate a PDF per provided directory, saving alongside screenshots"""
        try:
            # Read and normalize screenshot directories
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length)) if length else {}
            raw = data.get("screenshotDirs", [])
            dirs = []
            for d in raw:
                if isinstance(d, str) and d:
                    d2 = d.replace("\\", os.sep).replace("/", os.sep)
                    d2 = d2.lstrip(os.sep)
                    dirs.append(os.path.normpath(d2))
            if not dirs:
                raise ValueError("No screenshotDirs provided")
            # Generate one PDF per directory

            pdf_paths = []
            for d in dirs:
                # Locate folder
                full_d = os.path.join(PROJECT_ROOT, d)
                if not os.path.isdir(full_d):
                    full_d = os.path.join(os.getcwd(), d)
                if not os.path.isdir(full_d):
                    continue
                # Gather PNGs, sorted by creation time
                files = [f for f in os.listdir(full_d) if f.lower().endswith(".png")]
                files = sorted(
                    files, key=lambda f: os.path.getctime(os.path.join(full_d, f))
                )
                if not files:
                    continue
                # Create PDF in same folder
                pdf_path = os.path.join(full_d, "screenshots.pdf")
                c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
                w, h = landscape(A4)
                for fname in files:
                    img_path = os.path.join(full_d, fname)
                    c.drawImage(img_path, 0, 0, width=w, height=h)
                    c.showPage()
                c.save()
                # Log PDF creation path
                print(f"Generated PDF (generate_pdf): {pdf_path}")
                pdf_paths.append(pdf_path)
            if not pdf_paths:
                raise FileNotFoundError(
                    "No PDFs generated, directories empty or not found"
                )
            # Respond with generated paths
            self._set_headers(200)
            self.wfile.write(
                json.dumps({"success": True, "pdfPaths": pdf_paths}).encode()
            )
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def log_message(self, format, *args):
        # Custom logging to avoid cluttering the console
        return


def run_server():
    # Create necessary directories
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Templates dir: {TEMPLATES_DIR}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Public dir: {PUBLIC_DIR}")

    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    # Create a sample template if it doesn't exist
    sample_template = os.path.join(TEMPLATES_DIR, "screening_response_template.xml")
    if not os.path.exists(sample_template):
        print(f"Creating sample template at: {sample_template}")
        os.makedirs(os.path.dirname(sample_template), exist_ok=True)
        with open(sample_template, "w") as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>\n<root>\n    <UPI>{upi_timestamp}</UPI>\n    <Status>Pending</Status>\n    <Timestamp>{timestamp}</Timestamp>\n    <Details>\n        <Name>Test Transaction</Name>\n        <Amount>1000.00</Amount>\n        <Currency>USD</Currency>\n    </Details>\n</root>"""
            )

    # Start the server
    print(f"Starting server on port {PORT}")
    print(
        f"Templates directory contents: {os.listdir(TEMPLATES_DIR) if os.path.exists(TEMPLATES_DIR) else 'Not found'}"
    )

    with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"\nServing at http://localhost:{PORT}")
        print(f"Open http://localhost:{PORT}/tests-automation.html in your browser")
        print("Press Ctrl+C to stop the server\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, shutting down server...")
            # Gracefully stop serving
            httpd.shutdown()
        finally:
            print("Server has been stopped.")


if __name__ == "__main__":
    run_server()
