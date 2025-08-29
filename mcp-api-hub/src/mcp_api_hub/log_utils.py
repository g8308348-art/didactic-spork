from __future__ import annotations

import logging as _stdlib_logging
import sys
from typing import Any

import structlog


def setup_logging(level: str = "INFO") -> None:
    """Configure structlog and stdlib logging for JSON-ish logs safe for STDIO.

    Important for MCP stdio servers: avoid printing raw text to stdout; use logging.
    """
    processors = [
        structlog.processors.TimeStamper(fmt="iso", key="ts"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root = _stdlib_logging.getLogger()
    root.handlers.clear()
    handler = _stdlib_logging.StreamHandler(sys.stderr)
    handler.setFormatter(_stdlib_logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(getattr(_stdlib_logging, level.upper(), _stdlib_logging.INFO))


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
