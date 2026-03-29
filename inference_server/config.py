from __future__ import annotations

from pathlib import Path

from lidar_perception.config import InferenceServerConfig

DEFAULT_CONFIG_PATH = Path("configs/server.yaml")

__all__ = ["DEFAULT_CONFIG_PATH", "InferenceServerConfig", "load_server_config"]


def load_server_config(path: str | Path = DEFAULT_CONFIG_PATH) -> InferenceServerConfig:
    return InferenceServerConfig.from_yaml(path)
