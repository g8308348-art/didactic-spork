from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_api_hub.registry import autodiscover_and_register


def test_autodiscover_and_register_no_crash():
    mcp = FastMCP("test")
    # Should import modules under mcp_api_hub.tools and call their register()
    autodiscover_and_register("mcp_api_hub.tools", mcp)
    # After registration, at least one tool should exist (bpm)
    tools = [t.name for t in mcp._tools]  # type: ignore[attr-defined]
    assert any("bpm" in name for name in tools)
