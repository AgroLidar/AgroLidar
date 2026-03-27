from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_config_recursive(path: Path, stack: tuple[Path, ...]) -> dict[str, Any]:
    resolved_path = path.resolve()
    if resolved_path in stack:
        cycle = " -> ".join(str(item) for item in (*stack, resolved_path))
        raise ValueError(f"Detected cyclic base_config inheritance: {cycle}")

    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")

    path_stack = (*stack, resolved_path)

    path = resolved_path
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    if not isinstance(config, dict):
        raise TypeError(f"Config root must be a mapping in {path}, got {type(config).__name__}")

    base_config = config.pop("base_config", None)
    if base_config:
        base_path = (
            (path.parent / base_config).resolve()
            if not Path(base_config).is_absolute()
            else Path(base_config)
        )
        base = _load_config_recursive(base_path, path_stack)
        return _deep_merge(base, config)
    return config


def load_config(path: str | Path) -> dict[str, Any]:
    return _load_config_recursive(Path(path), ())
