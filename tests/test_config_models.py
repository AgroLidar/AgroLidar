from __future__ import annotations

from pathlib import Path

from lidar_perception.config import (
    EvalConfig,
    InferenceServerConfig,
    TrainConfig,
    load_yaml_with_inheritance,
)


def test_load_yaml_with_inheritance_merges_nested_mapping(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    child = tmp_path / "child.yaml"
    base.write_text(
        "model:\n  name: base\n  in_channels: 4\ndata:\n  batch_size: 2\n", encoding="utf-8"
    )
    child.write_text("base_config: base.yaml\nmodel:\n  name: child\n", encoding="utf-8")

    merged = load_yaml_with_inheritance(child)
    assert merged["model"]["name"] == "child"
    assert merged["model"]["in_channels"] == 4


def test_train_config_from_yaml_resolves_training_aliases() -> None:
    config = TrainConfig.from_yaml("configs/train.yaml")
    assert config.learning_rate == 0.001
    assert config.batch_size == 2


def test_eval_config_from_yaml_parses_evaluation_mapping() -> None:
    config = EvalConfig.from_yaml("configs/eval.yaml")
    assert config.evaluation["split"] == "test"
    assert config.batch_size == 2


def test_server_config_is_typed() -> None:
    config = InferenceServerConfig.from_yaml("configs/server.yaml")
    assert config.limits.max_batch_size == 16
    assert config.model.backend == "pytorch"
