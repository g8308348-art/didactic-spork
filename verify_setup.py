#!/usr/bin/env python3
"""Simple health-check script to verify the development environment.

Usage::
    python verify_setup.py

The script will:
1. Parse requirements.txt to retrieve all declared run-time dependencies.
2. Attempt to import each dependency and report any missing or
   mis-configured libraries.
3. Optionally run a lightweight Playwright sanity check (browser
   launch & close) so that we know the Playwright installation is fully
   functional. This part can be skipped with the CLI flag
   ``--skip-playwright`` because it downloads browser binaries on first
   run which can take a while.

Exit code is 0 if everything looks good, otherwise 1.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import List

REQ_FILE = Path(__file__).with_name("requirements.txt")

# ------------ Utility -------------------------------------------------------


def read_requirements() -> List[str]:
    """Return a list of top-level package names from *requirements.txt*."""
    packages: list[str] = []
    if not REQ_FILE.exists():
        print("⚠️  requirements.txt not found – skipping import checks")
        return packages

    for line in REQ_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # A requirement may be pinned (pkg==x.y), allow extras (pkg[foo]==x),
        # or specify a direct URL (git+...). We just need the import name.
        ambiguous_part = line.split("==")[0].split("[", 1)[0]
        # For URLs like "git+https://...#egg=foo" we fallback to egg name
        if "#egg=" in ambiguous_part:
            ambiguous_part = ambiguous_part.split("#egg=")[-1]
        # In most cases the import name is the same as package name, but
        # sometimes they differ (e.g. *Flask-Cors* → ``flask_cors``). We
        # handle the special-cases we know about, otherwise use the lower-case
        # dash-to-underscore mapping.
        mapping = {
            "flask-cors": "flask_cors",
            "python-dotenv": "dotenv",
        }
        import_name = mapping.get(ambiguous_part.lower(), ambiguous_part.lower().replace("-", "_"))
        packages.append(import_name)
    return packages


# ------------ Main logic ----------------------------------------------------


def run_checks(skip_playwright: bool) -> bool:
    """Return *True* on success, *False* if any check failed."""
    success = True

    print("🔍 Verifying declared Python dependencies…\n")
    for pkg in read_requirements():
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg} import ok")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"❌ Failed to import '{pkg}': {exc}")
            success = False

    if success:
        print("\nAll imports succeeded!")
    else:
        print(
            "\nSome imports failed – please install missing dependencies "
            "and/or check your PYTHONPATH."
        )

    if skip_playwright:
        return success

    # Extra Playwright smoke test
    try:
        from playwright.sync_api import sync_playwright  # type: ignore  # pylint: disable=import-outside-toplevel

        print("\n🚀 Launching a headless Chromium instance via Playwright…")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()
        print(f"✅ Playwright browser check ok – page title: '{title}'")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ Playwright smoke test failed: {exc}")
        success = False

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify project environment readiness.")
    parser.add_argument(
        "--skip-playwright",
        action="store_true",
        help="Skip the Playwright browser launch test.",
    )
    args = parser.parse_args()

    ok = run_checks(skip_playwright=args.skip_playwright)
    sys.exit(0 if ok else 1)
