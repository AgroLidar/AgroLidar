from pathlib import Path

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
