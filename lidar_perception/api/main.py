"""Canonical API app exported from inference_server.main.

This module is kept as a compatibility adapter for legacy imports.
"""

from __future__ import annotations

from inference_server.main import app, create_app

__all__ = ["app", "create_app"]
