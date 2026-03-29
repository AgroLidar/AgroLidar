"""
tests/safety/test_safety_config.py

Validates that SafetyConfig thresholds are sane and cannot be
accidentally relaxed below minimum values.

These tests MUST NEVER be skipped or have their thresholds reduced.
"""

import pytest
from pydantic import ValidationError

from lidar_perception.config import DANGEROUS_CLASSES, KnownClass, SafetyConfig


def test_default_safety_config_has_all_dangerous_classes() -> None:
    config = SafetyConfig()
    for cls in DANGEROUS_CLASSES:
        assert cls.value in config.dangerous_classes


def test_dangerous_recall_cannot_be_below_zero() -> None:
    with pytest.raises(ValidationError):
        SafetyConfig(min_dangerous_recall=-0.1)


def test_dangerous_recall_cannot_exceed_one() -> None:
    with pytest.raises(ValidationError):
        SafetyConfig(min_dangerous_recall=1.1)


def test_dangerous_fnr_threshold_is_strict() -> None:
    config = SafetyConfig()
    assert config.max_dangerous_fnr <= 0.05, (
        "FNR threshold must be <= 5% — relaxing this puts humans at risk"
    )


def test_min_recall_threshold_is_strict() -> None:
    config = SafetyConfig()
    assert config.min_dangerous_recall >= 0.95, (
        "Recall threshold must be >= 95% — relaxing this puts humans at risk"
    )


def test_human_in_known_classes() -> None:
    assert KnownClass.HUMAN in DANGEROUS_CLASSES


def test_animal_in_known_classes() -> None:
    assert KnownClass.ANIMAL in DANGEROUS_CLASSES


def test_vehicle_in_known_classes() -> None:
    assert KnownClass.VEHICLE in DANGEROUS_CLASSES
