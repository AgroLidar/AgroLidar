from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"  # nosec B104
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: str = "info"


@dataclass
class ModelConfig:
    checkpoint_path: str = "outputs/checkpoints/best.pt"
    config_path: str = "configs/base.yaml"
    device: str = "cpu"
    warmup_runs: int = 3
    backend: str = "pytorch"
    onnx_path: str = "outputs/onnx/model.onnx"


@dataclass
class LimitsConfig:
    max_batch_size: int = 16
    rate_limit_per_second: int = 100
    max_payload_mb: int = 50


@dataclass
class HealthConfig:
    p95_latency_threshold_ms: float = 200.0
    min_healthy_inferences: int = 10


@dataclass
class VectorDBConfig:
    enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    index_name: str = "agrolidar"


@dataclass
class InferenceServerConfig:
    server: ServerConfig
    model: ModelConfig
    limits: LimitsConfig
    health: HealthConfig
    vector_db: VectorDBConfig


DEFAULT_CONFIG_PATH = Path("configs/server.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        content = yaml.safe_load(handle) or {}
    if not isinstance(content, dict):
        raise TypeError(f"Server config root must be a mapping, got: {type(content).__name__}")
    return content


def load_server_config(path: str | Path = DEFAULT_CONFIG_PATH) -> InferenceServerConfig:
    raw = _load_yaml(Path(path))
    return InferenceServerConfig(
        server=ServerConfig(**raw.get("server", {})),
        model=ModelConfig(**raw.get("model", {})),
        limits=LimitsConfig(**raw.get("limits", {})),
        health=HealthConfig(**raw.get("health", {})),
        vector_db=VectorDBConfig(**raw.get("vector_db", {})),
    )
