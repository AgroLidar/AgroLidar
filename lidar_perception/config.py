from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class KnownClass(StrEnum):
    """All obstacle classes AgroLidar is trained to detect."""

    HUMAN = "human"
    ANIMAL = "animal"
    VEHICLE = "vehicle"
    ROCK = "rock"
    POST = "post"
    VEGETATION = "vegetation"


DANGEROUS_CLASSES: frozenset[KnownClass] = frozenset(
    {
        KnownClass.HUMAN,
        KnownClass.ANIMAL,
        KnownClass.VEHICLE,
    }
)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge mappings without mutating inputs."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_recursive(path: Path, stack: tuple[Path, ...]) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved in stack:
        cycle = " -> ".join(str(item) for item in (*stack, resolved))
        raise ValueError(f"Detected cyclic base_config inheritance: {cycle}")

    if not resolved.exists():
        raise FileNotFoundError(f"Config file not found: {resolved}")

    with resolved.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    if not isinstance(config, dict):
        raise TypeError(
            f"Config root must be a mapping in {resolved}, got {type(config).__name__}"
        )

    base_config = config.pop("base_config", None)
    if base_config:
        base_path = (
            (resolved.parent / base_config).resolve()
            if not Path(base_config).is_absolute()
            else Path(base_config)
        )
        base = _load_yaml_recursive(base_path, (*stack, resolved))
        return deep_merge(base, config)
    return config


def load_yaml_with_inheritance(path: str | Path) -> dict[str, Any]:
    """Load config YAML supporting `base_config` inheritance."""
    return _load_yaml_recursive(Path(path), ())


class DataConfig(BaseModel):
    """Dataset path configuration."""

    base_dataset_path: Path
    hard_cases_path: Path = Path("data/hard_cases")
    review_queue_path: Path = Path("data/review_queue")

    @field_validator("base_dataset_path", mode="before")
    @classmethod
    def path_must_exist(cls, v: str | Path) -> Path:
        p = Path(v)
        if not p.exists():
            raise ValueError(f"Dataset path does not exist: {p}")
        return p


class SafetyConfig(BaseModel):
    dangerous_classes: list[str] = [c.value for c in DANGEROUS_CLASSES]
    min_dangerous_recall: float = Field(default=0.95, ge=0.0, le=1.0)
    max_dangerous_fnr: float = Field(default=0.05, ge=0.0, le=1.0)
    max_latency_regression_ms: float = Field(default=10.0, gt=0.0)
    max_distance_error_m: float = Field(default=0.5, gt=0.0)


class ModelConfig(BaseModel):
    architecture: str = Field(description="Model class name in lidar_perception.models")
    input_voxel_size: float = Field(default=0.1, gt=0.0)
    bev_range_m: list[float] = Field(default=[0, -40, -3, 70.4, 40, 1])
    num_classes: int = Field(default=len(KnownClass), gt=0)
    pretrained_checkpoint: Path | None = None


class TrainConfig(BaseModel):
    model: dict[str, Any]
    data: dict[str, Any]
    training: dict[str, Any] = Field(default_factory=dict)
    safety: SafetyConfig = SafetyConfig()

    epochs: int = Field(gt=0, default=50)
    batch_size: int = Field(gt=0, default=8)
    learning_rate: float = Field(gt=0.0, default=1e-4)
    weight_decay: float = Field(ge=0.0, default=1e-4)
    device: Literal["cpu", "cuda", "mps"] = "cuda"
    num_workers: int = Field(ge=0, default=4)
    output_dir: Path = Path("outputs")
    experiment_tag: str = "default"
    seed: int = 42
    synthetic_data: dict[str, Any] = Field(default_factory=dict)
    config_path: Path | None = None

    @model_validator(mode="after")
    def apply_training_overrides(self) -> TrainConfig:
        training_cfg = dict(self.training)
        self.epochs = int(training_cfg.get("epochs", self.epochs))
        self.batch_size = int(training_cfg.get("batch_size", self.batch_size))
        self.learning_rate = float(
            training_cfg.get("learning_rate", training_cfg.get("lr", self.learning_rate))
        )
        self.weight_decay = float(training_cfg.get("weight_decay", self.weight_decay))
        if "num_workers" in self.data:
            self.num_workers = int(self.data["num_workers"])
        if "batch_size" in self.data:
            self.batch_size = int(self.data["batch_size"])
        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> TrainConfig:
        parsed = cls(**load_yaml_with_inheritance(path))
        return parsed.model_copy(update={"config_path": Path(path)})


class RetrainConfig(BaseModel):
    base_config: Path
    data: dict[str, Any]
    safety: SafetyConfig = SafetyConfig()
    hard_case_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    oversample_dangerous_classes: bool = True
    dangerous_class_weight: float = Field(default=2.0, gt=0.0)
    reviewed_only: bool = True
    only_high_conf_failures: bool = False
    candidate_tag: str = "candidate"
    output_dir: Path = Path("outputs")

    @classmethod
    def from_yaml(cls, path: str | Path) -> RetrainConfig:
        return cls(**load_yaml_with_inheritance(path))


class EvalConfig(BaseModel):
    model: dict[str, Any]
    data: dict[str, Any]
    evaluation: dict[str, Any] = Field(default_factory=dict)
    training: dict[str, Any] = Field(default_factory=dict)
    safety: SafetyConfig = SafetyConfig()

    checkpoint_path: Path | None = None
    batch_size: int = Field(gt=0, default=4)
    device: Literal["cpu", "cuda", "mps"] = "cuda"
    output_dir: Path = Path("outputs/reports")
    report_tag: str = "eval"
    fail_on_dangerous_fnr_above: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def infer_defaults(self) -> EvalConfig:
        if self.checkpoint_path is None:
            checkpoint = self.model.get("checkpoint")
            self.checkpoint_path = Path(checkpoint) if checkpoint else None
        self.batch_size = int(self.data.get("batch_size", self.batch_size))
        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> EvalConfig:
        return cls(**load_yaml_with_inheritance(path))


class InferenceConfig(BaseModel):
    checkpoint_path: Path = Path("outputs/checkpoints/best.pt")
    device: Literal["cpu", "cuda", "mps"] = "cuda"
    max_points: int = Field(default=200_000, gt=0)
    sensor_height_m: float = Field(default=1.5, gt=0.0)
    batch_timeout_ms: float = Field(default=50.0, gt=0.0)
    use_tensorrt: bool = False
    tensorrt_engine_path: Path | None = None

    @model_validator(mode="after")
    def tensorrt_requires_path(self) -> InferenceConfig:
        if self.use_tensorrt and self.tensorrt_engine_path is None:
            raise ValueError("tensorrt_engine_path required when use_tensorrt=True")
        return self


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: str = "info"
    cors_origins: list[str] = Field(default_factory=lambda: ["https://agro-lidar.vercel.app"])


class RuntimeModelConfig(BaseModel):
    checkpoint_path: str = "outputs/checkpoints/best.pt"
    config_path: str = "configs/base.yaml"
    device: str = "cpu"
    warmup_runs: int = 3
    backend: Literal["pytorch", "onnx"] = "pytorch"
    onnx_path: str = "outputs/onnx/model.onnx"


class LimitsConfig(BaseModel):
    max_batch_size: int = 16
    rate_limit_per_second: int = 100
    max_payload_mb: int = 50


class HealthConfig(BaseModel):
    p95_latency_threshold_ms: float = 200.0
    min_healthy_inferences: int = 10


class VectorDBConfig(BaseModel):
    enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    index_name: str = "agrolidar"


class InferenceServerConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    model: RuntimeModelConfig = Field(default_factory=RuntimeModelConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    health: HealthConfig = Field(default_factory=HealthConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> InferenceServerConfig:
        return cls(**load_yaml_with_inheritance(path))
