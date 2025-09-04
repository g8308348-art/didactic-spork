# Repository Guidelines

## Project Structure & Modules
- `flask_server.py` / `server.py`: HTTP API servers (Flask preferred). Serves `public/` and `/api` endpoints.
- `bpm/`, `firco/`, `utils/`: Core automation modules used by the API layer.
- `public/`: Frontend assets (HTML/CSS/JS).
- `input/`, `output/`: File I/O roots; override with `INCOMING_DIR` / `OUTPUT_DIR` env vars.
- `mcp-api-hub/`: Standalone MCP server (Python package with `src/` and `tests/`).
- `tests-automation/`: XML template helpers and dev tooling.
- `requirements.txt`, `.pylintrc`, `verify_setup.py`: Dependencies, lint config, env checks.

## Build, Test, and Dev Commands
- Create venv and install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `python -m playwright install chromium`
- Run the API (Flask):
  - `python flask_server.py` (listens on `http://0.0.0.0:8088`)
  - Legacy alternative: `python server.py`
- Quick environment check:
  - `python verify_setup.py` (use `--skip-playwright` to skip browser check)
- MCP subproject tests:
  - `cd mcp-api-hub && python -m venv .venv && source .venv/bin/activate && pip install -e . && pytest -q`

## Coding Style & Naming
- Python 3.x, 4-space indentation, UTF-8.
- Use type hints and concise docstrings for public functions.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_CASE` (see `.pylintrc`).
- Lint locally: `pylint server.py flask_server.py bpm/ firco/ utils/`.

## Testing Guidelines
- Framework: `pytest` for `mcp-api-hub/tests/` (`test_*.py`).
- Add unit tests alongside new tools under `mcp-api-hub/src/...`.
- For API changes, exercise `/api` and `/api/bpm` manually or via lightweight scripts; prefer deterministic tests where possible.

## Commit & Pull Requests
- Conventional commits observed in history: `feat:`, `fix:`, `style:`, etc.
  - Example: `feat: add BPM status mapping rules`.
- PRs should include:
  - Clear description (what/why), linked issues, and reproduction steps.
  - For UI/frontend changes in `public/`, add before/after screenshots.
  - Notes on env vars or migrations (e.g., `INCOMING_DIR`, `OUTPUT_DIR`).

## Security & Configuration
- Keep secrets in `.env`; never commit real credentials. Example: set `INCOMING_DIR`, `OUTPUT_DIR` and `BPM_URL` (for `mcp-api-hub`).
- Playwright downloads browsers on first run; pin versions via `requirements.txt` and re-run `python -m playwright install chromium` after upgrades.
