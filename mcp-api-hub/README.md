# mcp-api-hub

A generalized Python MCP server exposing multiple API tools via the Model Context Protocol (MCP). Includes:

- Structured config via Pydantic (`src/mcp_api_hub/config.py`)
- Structured JSON logging via `structlog` (`src/mcp_api_hub/logging.py`)
- Shared HTTP client with retries/timeouts (`src/mcp_api_hub/http_client.py`)
- Auto-discovery of tools (`src/mcp_api_hub/registry.py`)
- First tool: BPM search calling your Flask `/api/bpm` (`src/mcp_api_hub/tools/bpm.py`)
- Firco tool calling your Flask `/api` (`src/mcp_api_hub/tools/firco.py`)

## Install

```bash
# From project root
cd mcp-api-hub
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```env
DEFAULT_TIMEOUT=60
RETRY_MAX=3
LOG_LEVEL=INFO
BPM_URL=http://localhost:8088
# Optional credentials for underlying BPM system (if needed by Flask layer)
# BPM_USERNAME=
# BPM_PASSWORD=
```

## Run (stdio)

Using the console script installed by the package:

```bash
mcp-api-hub
```

Or run module directly:

```bash
python -m mcp_api_hub.server
```

You can test locally with MCP Inspector or wire into Claude Desktop.

### Claude Desktop config (~/.mcp/mcp.json)

```json
{
  "servers": {
    "mcp-api-hub": {
      "command": "mcp-api-hub",
      "env": {
        "BPM_URL": "http://localhost:8088",
        "DEFAULT_TIMEOUT": "60"
      }
    }
  }
}
```

## Tools

- `bpm_search_tool(payload)`
  - Input schema (Pydantic): `{ transactionId: string[3..50], marketType: string, timeoutSeconds?: number }`
  - Calls `POST {BPM_URL}/api/bpm`
  - Returns backend JSON with `_clientMeta` and `isError` added

- `firco_process_tool(payload)`
  - Input schema (Pydantic): `{ transaction: string, action: string, comment?: string, transactionType?: string, performOnLatest?: bool, timeoutSeconds?: number }`
  - Calls `POST {BPM_URL}/api`
  - Returns backend JSON with `_clientMeta` and `isError` added

## Tests

Run tests with pytest:

```bash
pytest -q
```

## Development

- Add new tool modules under `src/mcp_api_hub/tools/` with a `register(mcp)` function that decorates functions using `@mcp.tool()`.
- They will be auto-registered at startup.

*** cd C:\path\to\stt-murdock
python -c "import sys; sys.path.insert(0, r'mcp-api-hub\src'); from mcp_api_hub.server import main; main()" ***