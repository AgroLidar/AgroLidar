from __future__ import annotations

import tomllib
from pathlib import Path

import lidar_perception


def test_versions_are_synchronized() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    package_json = (root / "package.json").read_text(encoding="utf-8")
    version_file = (root / "VERSION").read_text(encoding="utf-8").strip()

    assert pyproject["project"]["version"] == version_file
    assert lidar_perception.__version__ == version_file
    assert f'"version": "{version_file}"' in package_json
