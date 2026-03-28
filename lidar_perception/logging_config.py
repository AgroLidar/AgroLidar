"""
lidar_perception/logging_config.py

Centralized structured logging for AgroLidar.
JSON output for field log aggregation. Human-readable for dev.

Usage:
    from lidar_perception.logging_config import configure_logging
    configure_logging()  # call once at app entry point
"""

from __future__ import annotations

import json
import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Designed for field deployment where logs are shipped to
    a central aggregator (e.g., Datadog, CloudWatch, Loki).
    """

    def format(self, record: logging.LogRecord) -> str:
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
        if hasattr(record, "extra"):
            payload.update(record.extra)  # type: ignore[arg-type]
        return json.dumps(payload, default=str)


def configure_logging(
    level: str | None = None,
    log_format: str | None = None,
    log_dir: Path = Path("outputs/logs"),
) -> None:
    """
    Configure application-wide logging for AgroLidar.

    Reads LOG_LEVEL and LOG_FORMAT from environment if not provided.
    Outputs to console (human format) and rotating file (JSON format).

    Args:
        level: Logging level. Defaults to LOG_LEVEL env var or 'INFO'.
        log_format: 'json' or 'human'. Defaults to LOG_FORMAT env var or 'human'.
        log_dir: Directory for log files. Created if it doesn't exist.
    """
    resolved_level = level or os.getenv("LOG_LEVEL", "INFO")
    resolved_format = log_format or os.getenv("LOG_FORMAT", "human")

    log_dir.mkdir(parents=True, exist_ok=True)

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": f"{__name__}.JSONFormatter"},
            "human": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": resolved_format,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": str(log_dir / "agrolidar.log"),
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": resolved_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {"level": "INFO", "propagate": True},
            "fastapi": {"level": "INFO", "propagate": True},
        },
    }

    logging.config.dictConfig(config)
