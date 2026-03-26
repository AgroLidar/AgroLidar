from pathlib import Path

import pytest

from lidar_perception.utils.config import load_config


def test_config_inheritance(tmp_path: Path):
    base = tmp_path / "base.yaml"
    child = tmp_path / "child.yaml"
    base.write_text("a: 1\nmodel:\n  x: 1\n", encoding="utf-8")
    child.write_text("base_config: base.yaml\nmodel:\n  y: 2\n", encoding="utf-8")
    cfg = load_config(child)
    assert cfg["a"] == 1
    assert cfg["model"]["x"] == 1
    assert cfg["model"]["y"] == 2


def test_config_inheritance_cycle_raises(tmp_path: Path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("base_config: b.yaml\na: 1\n", encoding="utf-8")
    b.write_text("base_config: a.yaml\nb: 2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="cyclic base_config"):
        load_config(a)


def test_config_missing_base_file_raises(tmp_path: Path):
    child = tmp_path / "child.yaml"
    child.write_text("base_config: missing.yaml\na: 1\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(child)


def test_config_non_mapping_root_raises(tmp_path: Path):
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(TypeError, match="Config root must be a mapping"):
        load_config(invalid)
