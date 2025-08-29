from __future__ import annotations

"""Compatibility shim.

Exports logging helpers from `log_utils` to avoid shadowing stdlib `logging`.
New code should import from `mcp_api_hub.log_utils` directly.
"""

from .log_utils import setup_logging, get_logger  # noqa: F401
