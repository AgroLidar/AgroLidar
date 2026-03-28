"""tests/unit/test_config.py — Pydantic config validation tests."""

import pytest
from pydantic import ValidationError

from lidar_perception.config import InferenceConfig


def test_inference_config_tensorrt_requires_path() -> None:
    with pytest.raises(ValidationError, match="tensorrt_engine_path"):
        InferenceConfig(use_tensorrt=True, tensorrt_engine_path=None)


def test_inference_config_defaults_are_valid() -> None:
    config = InferenceConfig()
    assert config.device == "cuda"
    assert config.max_points == 200_000


def test_safety_config_defaults_pass_all_gates() -> None:
    from lidar_perception.config import SafetyConfig

    config = SafetyConfig()
    assert config.min_dangerous_recall >= 0.95
    assert config.max_dangerous_fnr <= 0.05
