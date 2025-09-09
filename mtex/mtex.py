import os, argparse, logging, sys, time, json
from pathlib import Path
from contextlib import suppress
from playwright.sync_api import sync_playwright
from utils.utils import login_to

# --- Config (with environment variable support) ---
INCOMING_DIR = "input"
OUTPUT_DIR = "output"
LOG_FILE = "transactions.log"
TEST_URL = os.getenv("MTEX_URL", "https://cloud-ua1.com/mtexops/")
USERNAME = os.getenv("MTEX_USERNAME", "e72128")
PASSWORD = os.getenv("MTEX_PASSWORD", "123!")

# Dropdown selectors and values
DROPDOWN_BU = ("rc_select_0", "UAT")
DROPDOWN_WORKFLOW = ("rc_select_1", "ORI - TSF DEH ISO")

TRANSACTION_NOT_FOUND_STATUS = "transaction_not_found_in_any_tab"


# --- Logging Setup ---
def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging to file and console."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(process)03d] :: %(levelname)s :: %(name)s :: %(funcName)s :: %(message)s",
        datefmt="%X",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


# --- Main Script ---
def mtex_upload(url: str, username: str, password: str, bu: str, workflow: str, test_data_dir: str = None) -> dict:
    """Upload files to MTex and return status."""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        mtex_page = MtexPage(page)
        result = {"success": False, "message": "", "files_uploaded": []}

        try:
            # Login
            success = login_to(page, url, username, password)
            if not success:
                result["message"] = f"Login failed for {username} to {url}"
                return result
            result["success"] = True

            # Select dropdown options
            logging.info("Selecting dropdowns...")
            mtex_page.select_dropdown_option("rc_select_0", bu)
            mtex_page.select_dropdown_option("rc_select_1", workflow)

            # Wait
            page.wait_for_timeout(500)

            # Determine target directory
            if test_data_dir:
                target_dir = test_data_dir
            else:
                PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
                env_dir = os.environ.get("TEST_DATA_DIR")
                if env_dir and os.path.isdir(env_dir):
                    base_dir = env_dir
                elif os.path.isdir("C:/test_data"):
                    base_dir = "C:/test_data"
                else:
                    base_dir = os.path.join(PROJECT_ROOT, "test_data")
                if not os.path.isdir(base_dir):
                    raise FileNotFoundError(f"Test data directory not found: {base_dir}")
                subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
                if not subdirs:
                    raise FileNotFoundError(f"No subdirectories in test_data: {base_dir}")
                latest = sorted(subdirs)[-1]
                target_dir = os.path.join(base_dir, latest)

            logging.info(f"Uploading files from: {target_dir}")
            file_paths = [os.path.join(r, f) for r, _, files in os.walk(target_dir) for f in files]
            logging.info(f"Files to upload to MTex: {file_paths}")
            mtex_page.upload_files_and_click_button('input[name="file"]', file_paths, "button.ant-btn-primary")
            result["files_uploaded"] = file_paths

            # Screenshot
            screenshot_path = os.path.join(target_dir, "mtexops.png")
            page.screenshot(path=screenshot_path, full_page=True)
            logging.info(f"MTEx screenshot saved to: {screenshot_path}")
            result["screenshot_path"] = screenshot_path
            result["message"] = "Upload successful"

        except Exception as e:
            logging.exception("Error during MTex upload")
            result["message"] = str(e)
        finally:
            with suppress(Exception):
                context.close()
            with suppress(Exception):
                browser.close()
        return result


def main() -> int:
    """Main entry point with argument parsing."""
    # Pre-parser for log level
    pre = argparse.ArgumentParser(add_help=True)
    pre.add_argument("--log-level", default="DEBUG", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    pre_args, _ = pre.parse_known_args()

    setup_logging(pre_args.log_level)

    # Full parser
    parser = argparse.ArgumentParser(description="Upload files to MTex")
    parser.add_argument("--url", default=TEST_URL, help="MTex URL")
    parser.add_argument("--username", default=USERNAME, help="Login username")
    parser.add_argument("--password", default=PASSWORD, help="Login password")
    parser.add_argument("--bu", default="UAT", help="Business Unit (e.g., UAT)")
    parser.add_argument("--workflow", default="ORI - TSF DEH ISO", help="Workflow selection")
    parser.add_argument("--test-data-dir", help="Override test data directory")
    parser.add_argument("--log-level", default=pre_args.log_level, help="Logging level")

    args = parser.parse_args()

    # Measure duration
    t_start = time.perf_counter()
    result = mtex_upload(args.url, args.username, args.password, args.bu, args.workflow, args.test_data_dir)
    t_end = time.perf_counter()

    logging.info(f"Duration: {t_end - t_start:.3f}s")
    print(json.dumps(result))
    return 0 if result["success"] else 1


def main_old(test_data_dir_override=None):
    setup_logging()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
            context = browser.new_context()
            page = context.new_page()
            mtex_page = MtexPage(page)

            # Login
            mtex_page.login(TEST_URL, USERNAME, PASSWORD)

            # Select dropdown options
            logging.info("Selecting dropdowns...")
            mtex_page.select_dropdown_option(*DROPDOWN_BU)
            mtex_page.select_dropdown_option(*DROPDOWN_WORKFLOW)

            # Wait (if needed)
            page.wait_for_timeout(500)

            # Determine target directory for upload
            if test_data_dir_override:
                target_dir = test_data_dir_override
            else:
                # Base test data dir: env override, C:/test_data, or project/test_data
                PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
                env_dir = os.environ.get("TEST_DATA_DIR")
                if env_dir and os.path.isdir(env_dir):
                    base_dir = env_dir
                elif os.path.isdir("C:/test_data"):
                    base_dir = "C:/test_data"
                else:
                    base_dir = os.path.join(PROJECT_ROOT, "test_data")
                if not os.path.isdir(base_dir):
                    raise FileNotFoundError(
                        f"Test data directory not found: {base_dir}"
                    )
                # Pick the latest timestamped subfolder
                subdirs = [
                    d
                    for d in os.listdir(base_dir)
                    if os.path.isdir(os.path.join(base_dir, d))
                ]
                if not subdirs:
                    raise FileNotFoundError(
                        f"No subdirectories in test_data: {base_dir}"
                    )
                latest = sorted(subdirs)[-1]
                target_dir = os.path.join(base_dir, latest)
            logging.info(f"Uploading files from: {target_dir}")
            # Collect files in target directory
            file_paths = [
                os.path.join(r, f) for r, _, files in os.walk(target_dir) for f in files
            ]
            logging.info(f"Files to upload to MTex: {file_paths}")
            mtex_page.upload_files_and_click_button(
                'input[name="file"]', file_paths, "button.ant-btn-primary"
            )
            # Take a full-page screenshot after scrolling element into view, saving to target_dir
            screenshot_path = os.path.join(target_dir, "mtexops.png")
            page.screenshot(path=screenshot_path, full_page=True)
            logging.info(f"MTEx screenshot saved to: {screenshot_path}")

        except Exception as e:
            logging.exception("Unhandled exception occurred")
        finally:
            context.close()
            # browser.close()


if __name__ == "__main__":
    sys.exit(main())
