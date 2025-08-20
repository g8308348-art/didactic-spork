from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def login_to(page: Page, url: str, username: str, password: str) -> bool:
    """Generic login flow

    Returns True on success, False on timeout or failure. Logs details.
    Clears cookies and site storage for the target origin before login.
    """
    try:
        # Clear cookies for a clean session
        try:
            page.context.clear_cookies()
            logging.debug("Cleared context cookies before login.")
        except Exception as e:
            logging.warning("Could not clear cookies before login: %s", e)

        # Navigate to the origin and clear site storage (localStorage, sessionStorage, indexedDB)
        try:
            parsed = urlparse(url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            page.goto(origin)
            page.wait_for_load_state("domcontentloaded")
            page.evaluate(
                """
                (() => {
                  try { localStorage.clear(); } catch (_) {}
                  try { sessionStorage.clear(); } catch (_) {}
                  if (window.indexedDB && indexedDB.databases) {
                    return indexedDB.databases().then(dbs => Promise.all(
                      dbs.map(db => indexedDB.deleteDatabase(db.name))
                    )).catch(() => {});
                  }
                  return null;
                })()
                """
            )
            logging.debug("Cleared site storage for origin %s before login.", origin)
        except Exception as e:
            logging.warning("Could not clear site storage before login: %s", e)

        logging.debug("Logging to %s as %s.", url, username)
        page.goto(url)
        expect(page).to_have_title("State Street Login")
        page.fill("input[name='username']", username)
        page.fill("input[name='PASSWORD']", password)
        page.click("input[type='submit'][value='Submit']")
        page.wait_for_load_state("networkidle")
        logging.debug("We are in %s as %s.", url, username)
        return True
    except PlaywrightTimeoutError as e:
        logging.error("Failed to login to %s as %s", url, username)
        logging.error("Login error: %s", e)
        return False


def archive_screenshots(transaction: str) -> Optional[Path]:
    """Move all PNG screenshots in CWD to screenshots/{date}_{transaction} and return the folder path.

    The date format is YYYYMMDD_HHMMSS for uniqueness.
    Always returns the destination directory (created), even if nothing was moved.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = Path("screenshots") / f"{timestamp}_{transaction}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    moved_any = False
    for png in Path(".").glob("*.png"):
        try:
            shutil.move(str(png), dest_dir / png.name)
            moved_any = True
        except Exception as e:  # pragma: no cover - best-effort archival
            logging.warning("Could not move %s: %s", png, e)

    if moved_any:
        logging.debug("Screenshots archived to %s", dest_dir)
    else:
        logging.debug("No screenshots found to archive.")
    return dest_dir


def clear_existing_screenshots() -> None:
    """Delete all PNG screenshots in the current working directory."""
    try:
        removed_any = False
        for png in Path(".").glob("*.png"):
            try:
                png.unlink()
                removed_any = True
            except Exception as e:  # pragma: no cover - best-effort cleanup
                logging.warning("Could not delete %s: %s", png, e)
        if removed_any:
            logging.debug("Cleared existing PNG screenshots before run.")
        else:
            logging.debug("No PNG screenshots to clear before run.")
    except Exception as e:  # pragma: no cover
        logging.warning("Failed to clear existing screenshots: %s", e)
