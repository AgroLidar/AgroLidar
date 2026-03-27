import json
from pathlib import Path

import numpy as np

from lidar_perception.data.datasets import build_dataset


def test_manifest_dataset_loads_bin(tmp_path: Path):
    points = np.random.rand(20, 4).astype("float32")
    bin_path = tmp_path / "frame.bin"
    points.tofile(bin_path)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"sample_id": "s1", "point_cloud": str(bin_path)}) + "\n", encoding="utf-8"
    )

    cfg = {
        "dataset_type": "manifest",
        "manifest_path": str(manifest),
        "point_cloud_range": [-10, -10, -3, 10, 10, 3],
        "grid_size": [32, 32],
        "preprocessing": {"enabled": False},
    }
    ds = build_dataset(cfg, "test")
    sample = ds[0]
    assert sample["sample_id"] == "s1"
    assert sample["bev"].ndim == 3
