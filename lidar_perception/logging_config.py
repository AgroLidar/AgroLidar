"""Centralized structured logging for the AgroLidar perception system."""

from __future__ import annotations

import json
import logging
import logging.config
from pathlib import Path
from typing import Any


LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "lidar_perception.logging_config.JSONFormatter",
        },
        "human": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "human",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "outputs/logs/agrolidar.log",
            "maxBytes": 10_485_760,
            "backupCount": 5,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for machine-parseable field logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a ``logging.LogRecord`` into a JSON string.

        Args:
            record: Standard log record emitted by the Python logging framework.

        Returns:
            A JSON serialized string containing timestamp, level, logger, and context fields.
        """
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    Args:
        level: Logging level string (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``).
    """
    Path("outputs/logs").mkdir(parents=True, exist_ok=True)
    LOGGING_CONFIG["root"]["level"] = level
    logging.config.dictConfig(LOGGING_CONFIG)
