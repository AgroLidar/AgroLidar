from __future__ import annotations

from pathlib import Path
from typing import Any

from lidar_perception.config import (
    EvalConfig,
    InferenceServerConfig,
    TrainConfig,
    load_yaml_with_inheritance,
)


def load_config(path: str | Path) -> dict[str, Any]:
    """Backward-compatible config loader returning merged mapping."""
    return load_yaml_with_inheritance(path)


def load_train_config(path: str | Path) -> TrainConfig:
    return TrainConfig.from_yaml(path)


def load_eval_config(path: str | Path) -> EvalConfig:
    return EvalConfig.from_yaml(path)


def load_server_config(path: str | Path) -> InferenceServerConfig:
    return InferenceServerConfig.from_yaml(path)
