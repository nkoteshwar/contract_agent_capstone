"""
Training Pipeline Shared Utilities
Centralizes logging setup and common abstractions (DRY principle).
Reuses the structured JSON logging convention from backend/shared/utils/logger.py.
"""

import logging
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, TypeVar, Generic, Optional, List, Any

# ---------------------------------------------------------------------------
# Compatibility patch for set_submodule 
# (missing in some torch/transformers pairs used by bitsandbytes)
# ---------------------------------------------------------------------------
import torch.nn as nn
if not hasattr(nn.Module, "set_submodule"):
    def set_submodule(self, target: str, module: nn.Module):
        segments = target.split(".")
        arm = self
        for name in segments[:-1]:
            arm = getattr(arm, name)
        setattr(arm, segments[-1], module)
    nn.Module.set_submodule = set_submodule


T = TypeVar("T")


# ---------------------------------------------------------------------------
# Logging — DRY: single setup function, mirrors backend/shared/utils/logger.py
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """
    Structured JSON log formatter.
    Reuses the same format as backend/shared/utils/logger.py for consistency.
    Logs only to stderr (never to browser console). Safe for server-side use.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_training_logging(level: int = logging.INFO) -> None:
    """
    Configure Python logging with JSON formatter.
    Must be called once at script entry — all scripts share this setup.
    SECURITY: All logs go to stderr, never to browser console or stdout.
    """
    handler = logging.StreamHandler()  # defaults to stderr
    handler.setFormatter(JsonFormatter())
    logging.root.setLevel(level)
    logging.root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """
    Get a pre-configured logger instance.
    DRY: mirrors backend/shared/utils/logger.py::get_logger().
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Generic Registry — DRY: replaces DatasetRegistry + FormatterRegistry
# Open/Closed: register new items without modifying existing code.
# Mirrors IAgentRegistry from backend/agents/supervisor/interfaces.py
# ---------------------------------------------------------------------------

class Registry(Generic[T]):
    """
    Generic type-safe registry for pluggable strategies.
    Eliminates duplicate DatasetRegistry / FormatterRegistry classes (DRY).

    Usage:
        registry = Registry[IDatasetDownloader]()
        registry.register("cuad", CUADDownloader())
        downloader = registry.get("cuad")
    """

    def __init__(self):
        self._items: Dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        """Register an item by name."""
        self._items[name] = item

    def get(self, name: str) -> Optional[T]:
        """Retrieve an item by name."""
        return self._items.get(name)

    def list_all(self) -> List[str]:
        """List all registered names."""
        return list(self._items.keys())

    def get_all(self) -> Dict[str, T]:
        """Return all registered items."""
        return dict(self._items)

    def __contains__(self, name: str) -> bool:
        return name in self._items

    def __len__(self) -> int:
        return len(self._items)
