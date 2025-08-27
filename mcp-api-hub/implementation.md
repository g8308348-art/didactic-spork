Generalized Python MCP Server — Step-by-Step Implementation Plan

Goal: build a single, reusable MCP server that can expose multiple tools/endpoints (e.g., your /api/bpm plus other APIs) with clean module boundaries, typed schemas, robust error handling, and easy client setup.

1) Name the project & repo

Pick a neutral, extensible name, e.g. mcp-api-hub, mcp-toolbox, or mcp-gateway.

Target Python ≥3.9. Use pip for env & packaging.

Base on the official MCP Python SDK (stdio transport by default). 
GitHub
Model Context Protocol

Actions

mkdir mcp-api-hub && cd mcp-api-hub

uv venv && source .venv/bin/activate (or python -m venv .venv)

uv pip install mcp pydantic python-dotenv httpx tenacity structlog pytest responses

The Server Quickstart shows stdio-based servers and how to connect from clients like Claude Desktop. 
Model Context Protocol
+1

2) Repository layout (generic, multi-tool)
mcp-api-hub/
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ src/
│  └─ mcp_api_hub/
│     ├─ __init__.py
│     ├─ server.py               # boots MCP server, auto-registers tools
│     ├─ config.py               # Pydantic settings, env/.env
│     ├─ logging.py              # structlog/json logging
│     ├─ http_client.py          # shared HTTPX client (timeouts/retries)
│     ├─ registry.py             # Tool registry/auto-discovery
│     └─ tools/
│        ├─ __init__.py
│        ├─ bpm.py               # /api/bpm tool(s)
│        ├─ foo.py               # other endpoint families
│        └─ bar/
│           ├─ __init__.py
│           └─ search.py         # nested package if helpful
└─ tests/
   ├─ test_bpm_tool.py
   ├─ test_registry.py
   └─ conftest.py


This keeps server bootstrapping separate from tool modules, and shares a hardened HTTP client. The MCP SDK natively supports stdio/SSE/HTTP transports when/if you expand. 
GitHub

3) Project config & packaging

pyproject.toml: declare deps, and a console script mcp-api-hub = mcp_api_hub.server:main to run via PATH.

Provide .env.example for endpoint URLs, auth, and timeouts; load with python-dotenv.

Claude Desktop & Claude Code can load local MCP servers via config; we’ll expose a single binary/entrypoint for simplicity. 
Model Context Protocol
Anthropic

4) Settings & environment

Create config.py:

BaseSettings (Pydantic) with fields like DEFAULT_TIMEOUT=60, RETRY_MAX=3, BASE_URLS per service (e.g., BPM_BASE_URL), and optional API_KEY/basic creds per service.

Support per-tool overrides (e.g., BPM_TIMEOUT, BPM_AUTH_MODE).

This centralizes env handling and keeps secrets out of code. (Load .env at startup.)

5) Structured logging

Create logging.py:

Configure structlog for JSON logs with timestamps, levels, and requestId correlation.

Avoid logging secrets; include timing (ms) and httpStatus in results.

6) Shared HTTP client

Create http_client.py:

Build a single HTTPX client with:

Default timeout from settings (overrideable per call).

tenacity retries (idempotent POST only if you know the backend is safe; otherwise retry on connect/read).

Optional auth headers (API key / Basic) injected per service.

Return parsed JSON or a normalized error object when response is non-JSON.

This isolates networking and makes tools compact & consistent.

7) Tool registry & auto-discovery

Create registry.py:

A small decorator @tool_def(name, description, schema) that stores callables in a registry.

An autodiscover("mcp_api_hub.tools") to import all modules under tools/ and register them.

In server.py, iterate the registry to register with MCP (Server + @server.tool) at runtime.

Tools must advertise name/description/input schema; the MCP SDK exposes them to clients exactly as defined. 
GitHub

8) Implement your first generalized tool (BPM)

In tools/bpm.py:

Define a Pydantic input model (e.g., transactionId, marketType, optional timeoutSeconds).

Validate formats (mirrors backend) and call the shared client to POST to /api/bpm.

Forward the backend’s structured JSON untouched; add _clientMeta = {endpoint, elapsedMs, httpStatus}.

Return isError=True if HTTP ≥400 or response JSON says "status":"error".

Mirrors the pattern used in the Server Quickstart & tools guidance (schema-led). 
Model Context Protocol
Anthropic

9) Add more endpoints as tools

For each API family, create a module under tools/:

tools/foo.py with tools: foo.create, foo.search, foo.delete

Or nest: tools/bar/search.py exporting bar.search
Each tool follows the same template: typed input → call shared client → normalized output → MCP ToolResponse.

Claude tool use expects clear names/descriptions and accurate input schemas. 
Anthropic
+1

10) MCP server bootstrap

Create server.py:

Initialize Server("mcp-api-hub").

Load env & logging.

autodiscover() tool modules, then register each tool with MCP’s Python SDK.

server.run_stdio() to serve over stdio (the most broadly compatible transport for local clients). 
GitHub
Model Context Protocol

11) Client configuration (Claude Desktop / Claude Code)

Create ~/.mcp/mcp.json (or use Claude Code’s setup) with:

{
  "servers": {
    "mcp-api-hub": {
      "command": "mcp-api-hub",
      "env": {
        "BPM_BASE_URL": "http://localhost:5000",
        "BPM_API_KEY": "",
        "DEFAULT_TIMEOUT": "60"
      }
    }
  }
}


Then start Claude Desktop or Claude Code; you should see the server & tools available. 
Model Context Protocol
Anthropic

Prefer MCP Inspector for local interactive testing (connect over stdio). 
Model Context Protocol
GitHub

Claude Desktop also supports “Desktop Extensions” to install/manage local MCP servers more easily in newer builds. 
Anthropic Help Center

12) Tests

Unit tests (pytest + responses) for tools:

success (200 JSON)

backend error (4xx/5xx JSON)

non-JSON bodies

client timeout/connection error

Assert the tool returns isError appropriately and includes _clientMeta.

Optional: a smoke script using MCP Inspector to call each tool.

Inspector docs & repos outline local wiring and security considerations when proxying to local processes. 
Model Context Protocol
GitHub

13) Packaging & distribution

pyproject.toml with entry_points → mcp-api-hub.

uv build (or pipx install .) to get a global CLI.

Provide a minimal Dockerfile if you want to ship as a containerized stdio server (some clients can exec the binary inside a container or you can run it locally and connect).

The MCP client quickstart shows how clients connect regardless of language/packaging; stdio keeps things portable. 
Model Context Protocol

14) Observability & DX

Add per-tool timing, requestId, and service/endpoint tags in logs.

Make a --debug flag to turn on verbose logging.

Provide GET /healthz for your APIs (if you expose any local HTTP surfaces later).

Keep a /docs section in README with examples of tool inputs for the client.

15) Security & hardening

Never log secrets; mask auth headers.

Enforce timeouts and size limits on responses.

If you later enable remote MCP connectivity (SSE/HTTP or via Claude’s MCP connector), review auth and network ACLs; treat Inspector proxies as sensitive dev tools. 
Anthropic
GitHub

16) Roadmap (nice-to-have)

Add resources/prompts (not just tools) to the server if useful (MCP supports these natively). 
GitHub

Generate tool schemas from OpenAPI specs to reduce drift.

Per-service rate limiting and circuit breakers in http_client.py.

Optional non-stdio transports (SSE/streamable HTTP) when integrating beyond local clients. 
GitHub

17) Minimal “definition of done”

mcp-api-hub starts cleanly and lists multiple tools in the MCP client.

Each tool validates inputs, calls its endpoint, returns normalized JSON + _clientMeta, and sets isError correctly.

Tests cover success/error/timeout paths.

README shows install, config (mcp.json), and example tool invocations through MCP Inspector and Claude Desktop/Code. 
Model Context Protocol
+1
Anthropic