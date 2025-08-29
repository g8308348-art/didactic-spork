from __future__ import annotations

import os

from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

from .config import settings
from .logging import setup_logging, get_logger
from .registry import autodiscover_and_register


def main() -> None:
    # Load environment and configure logging early
    load_dotenv()
    setup_logging(settings.LOG_LEVEL)
    log = get_logger(__name__)

    # Initialize MCP server
    mcp = FastMCP(name="mcp-api-hub")

    # Autodiscover and register tools
    autodiscover_and_register("mcp_api_hub.tools", mcp)

    log.info("Starting MCP server (stdio)", server_name="mcp-api-hub")
    mcp.run()


if __name__ == "__main__":
    main()
