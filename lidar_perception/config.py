"""
lidar_perception/config.py

Strongly-typed, validated configuration for all AgroLidar pipelines.

All YAML config files must be loaded through these models.
Direct dict access to raw YAML is FORBIDDEN in this codebase.

Example:
    config = TrainConfig.from_yaml("configs/train.yaml")
    learning_rate = config.learning_rate  # typed, validated, IDE-autocompleted
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Shared sub-configs
# ---------------------------------------------------------------------------


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
    """
    Safety thresholds for model promotion and evaluation.

    These values define the minimum acceptable safety bar for
    any model to enter production. Do NOT relax these thresholds
    without explicit team review and documented justification.
    """

    dangerous_classes: list[str] = [c.value for c in DANGEROUS_CLASSES]
    min_dangerous_recall: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Minimum recall on dangerous classes (human, animal, vehicle)",
    )
    max_dangerous_fnr: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Maximum false-negative rate on dangerous classes",
    )
    max_latency_regression_ms: float = Field(
        default=10.0,
        gt=0.0,
        description="Max allowed inference latency increase vs production (ms)",
    )
    max_distance_error_m: float = Field(
        default=0.5,
        gt=0.0,
        description="Max mean absolute distance error for obstacle localization (m)",
    )


class ModelConfig(BaseModel):
    """Deep learning model architecture configuration."""

    architecture: str = Field(description="Model class name in lidar_perception.models")
    input_voxel_size: float = Field(default=0.1, gt=0.0)
    bev_range_m: list[float] = Field(default=[0, -40, -3, 70.4, 40, 1])
    num_classes: int = Field(default=len(KnownClass), gt=0)
    pretrained_checkpoint: Path | None = None


# ---------------------------------------------------------------------------
# Pipeline configs
# ---------------------------------------------------------------------------


class TrainConfig(BaseModel):
    """Full configuration for the training pipeline (scripts/train.py)."""

    model: ModelConfig
    data: DataConfig
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

    @classmethod
    def from_yaml(cls, path: str | Path) -> TrainConfig:
        """Load and validate training config from a YAML file."""
        with open(path, encoding="utf-8") as f:
            return cls(**yaml.safe_load(f))


class RetrainConfig(BaseModel):
    """Configuration for hard-case-aware retraining (scripts/retrain.py)."""

    base_config: Path
    data: DataConfig
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
        with open(path, encoding="utf-8") as f:
            return cls(**yaml.safe_load(f))


class EvalConfig(BaseModel):
    """Configuration for model evaluation (scripts/evaluate.py)."""

    checkpoint_path: Path
    data: DataConfig
    safety: SafetyConfig = SafetyConfig()

    batch_size: int = Field(gt=0, default=4)
    device: Literal["cpu", "cuda", "mps"] = "cuda"
    output_dir: Path = Path("outputs/reports")
    report_tag: str = "eval"
    fail_on_dangerous_fnr_above: float = Field(default=0.10, ge=0.0, le=1.0)

    @classmethod
    def from_yaml(cls, path: str | Path) -> EvalConfig:
        with open(path, encoding="utf-8") as f:
            return cls(**yaml.safe_load(f))


class InferenceConfig(BaseModel):
    """Configuration for the FastAPI inference server."""

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
