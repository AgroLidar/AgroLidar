"""Strongly-typed, validated configuration models for AgroLidar pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataConfig(BaseModel):
    """Dataset path configuration."""

    model_config = ConfigDict(extra="allow")

    base_dataset_path: Path
    hard_cases_path: Path = Path("data/hard_cases")
    review_queue_path: Path = Path("data/review_queue")

    @field_validator("base_dataset_path", mode="before")
    @classmethod
    def must_exist(cls, value: str | Path) -> Path:
        """Validate that the base dataset path exists.

        Args:
            value: Input path from user config.

        Returns:
            Normalized path object.

        Raises:
            ValueError: If the target path does not exist.
        """
        path = Path(value)
        if not path.exists():
            raise ValueError(f"Dataset path does not exist: {path}")
        return path


class SafetyConfig(BaseModel):
    """Safety thresholds for model promotion decisions."""

    model_config = ConfigDict(extra="allow")

    dangerous_classes: list[str] = ["human", "animal", "vehicle"]
    max_dangerous_fnr: float = Field(0.05, ge=0.0, le=1.0)
    min_dangerous_recall: float = Field(0.95, ge=0.0, le=1.0)
    max_latency_regression_ms: float = Field(10.0, gt=0.0)


class TrainConfig(BaseModel):
    """Configuration for model training pipeline."""

    model_config = ConfigDict(extra="allow")

    model_architecture: str
    epochs: int = Field(gt=0)
    batch_size: int = Field(gt=0)
    learning_rate: float = Field(gt=0.0)
    output_dir: Path = Path("outputs")
    data: DataConfig
    safety: SafetyConfig = SafetyConfig()
    device: Literal["cpu", "cuda", "mps"] = "cuda"
    seed: int = 42
    config_path: Path | None = None

    @classmethod
    def from_yaml(cls, path: str | Path) -> "TrainConfig":
        """Load and validate training config from YAML file.

        Args:
            path: YAML file path.

        Returns:
            Validated ``TrainConfig`` instance.
        """
        with Path(path).open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        mapped = dict(raw)
        model = raw.get("model", {})
        training = raw.get("training", {})
        data = raw.get("data", {})
        mapped.setdefault("model_architecture", model.get("architecture", model.get("name", "pointpillars_bev")))
        mapped.setdefault("epochs", training.get("epochs", 1))
        mapped.setdefault("batch_size", data.get("batch_size", training.get("batch_size", 1)))
        mapped.setdefault("learning_rate", training.get("learning_rate", training.get("lr", 1e-3)))
        mapped.setdefault("output_dir", raw.get("output_dir", "outputs"))
        mapped.setdefault("device", raw.get("device", "cuda"))
        mapped.setdefault("seed", int(raw.get("seed", 42)))
        mapped.setdefault("data", {"base_dataset_path": data.get("root_dir", "data")})
        cfg = cls(**mapped)
        cfg.config_path = Path(path)
        return cfg


class RetrainConfig(BaseModel):
    """Configuration for hard-case-aware retraining pipeline."""

    model_config = ConfigDict(extra="allow")

    base_config: Path
    hard_case_ratio: float = Field(0.3, ge=0.0, le=1.0)
    oversample_dangerous_classes: bool = True
    dangerous_class_weight: float = Field(2.0, gt=0.0)
    reviewed_only: bool = True
    only_high_conf_failures: bool = False
    candidate_tag: str = "candidate"
    data: DataConfig
    safety: SafetyConfig = SafetyConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RetrainConfig":
        """Load and validate retraining config from YAML file.

        Args:
            path: YAML file path.

        Returns:
            Validated ``RetrainConfig`` instance.
        """
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls(**(yaml.safe_load(handle) or {}))
