from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Callable, Optional

from .logging import get_logger

logger = get_logger(__name__)


def autodiscover_and_register(package: str, mcp_instance) -> None:
    """Import all submodules in `package` and call their `register(mcp)` if present.

    This keeps tool modules self-contained while allowing dynamic registration.
    """
    pkg = importlib.import_module(package)
    if not hasattr(pkg, "__path__"):
        logger.warning("Package %s has no __path__ for discovery", package)
        return

    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            mod = importlib.import_module(name)
            _register_module(mod, mcp_instance)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed importing tool module %s: %s", name, exc)


def _register_module(mod: ModuleType, mcp_instance) -> None:
    register: Optional[Callable] = getattr(mod, "register", None)
    if callable(register):
        register(mcp_instance)
        logger.info("Registered tools from module", module=mod.__name__)
