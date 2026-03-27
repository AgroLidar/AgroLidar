import json
from pathlib import Path

import numpy as np

from lidar_perception.data.datasets import build_dataset
from lidar_perception.data.hard_case_dataset import (
    CompositeTrainingDataset,
    ReviewedHardCaseDataset,
)


def _cfg(tmp_path: Path) -> dict:
    return {
        "dataset_type": "reviewed_hard_cases",
        "class_names": ["human", "animal", "vehicle", "post", "rock"],
        "segmentation_classes": [
            "background",
            "traversable_ground",
            "vegetation",
            "vehicle",
            "human",
            "obstacle",
        ],
        "point_cloud_range": [-10, -10, -3, 10, 10, 3],
        "grid_size": [32, 32],
        "preprocessing": {"enabled": False},
        "augmentations": {"enabled": False},
        "hard_case": {
            "dirs": [
                str(tmp_path / "data" / "hard_cases"),
                str(tmp_path / "data" / "review_queue"),
            ],
            "manifests": [],
            "only_reviewed": True,
            "only_high_conf_failures": False,
            "min_failure_confidence": 0.5,
        },
    }


def test_reviewed_hard_case_dataset_filters_and_handles_missing_labels(tmp_path: Path):
    hard = tmp_path / "data" / "hard_cases"
    hard.mkdir(parents=True)

    pts = np.random.rand(64, 4).astype("float32")
    pc = hard / "sample.bin"
    pts.tofile(pc)

    # reviewed sample with missing labels/boxes should still load.
    rec = {"sample_id": "h1", "point_cloud": str(pc), "reviewed": True, "failure_confidence": 0.9}
    (hard / "h1.json").write_text(json.dumps(rec), encoding="utf-8")

    # unreviewed should be filtered out.
    rec2 = {"sample_id": "h2", "point_cloud": str(pc), "reviewed": False, "failure_confidence": 0.9}
    (hard / "h2.json").write_text(json.dumps(rec2), encoding="utf-8")

    ds = ReviewedHardCaseDataset(_cfg(tmp_path), split="train")
    assert len(ds) == 1
    sample = ds[0]
    assert sample["sample_id"] == "h1"
    assert sample["boxes"].shape[0] == 0
    assert sample["labels"].shape[0] == 0


def test_composite_dataset_mixes_base_and_hard_cases_with_weighting(tmp_path: Path):
    base_cfg = {
        "dataset_type": "synthetic_agriculture",
        "train_size": 4,
        "val_size": 1,
        "test_size": 1,
        "num_points": 200,
        "class_names": ["human", "animal", "vehicle", "post", "rock"],
        "segmentation_classes": [
            "background",
            "traversable_ground",
            "vegetation",
            "vehicle",
            "human",
            "obstacle",
        ],
        "point_cloud_range": [-10, -10, -3, 10, 10, 3],
        "grid_size": [32, 32],
        "max_objects": 3,
        "augmentations": {"enabled": False},
        "simulation": {"terrain_variation": 0.0, "vegetation_density": 0.0},
        "preprocessing": {"enabled": False},
    }
    base_ds = build_dataset(base_cfg, "train")

    hard_cfg = _cfg(tmp_path)
    hard = tmp_path / "data" / "hard_cases"
    hard.mkdir(parents=True, exist_ok=True)
    pts = np.random.rand(64, 4).astype("float32")
    pc = hard / "sample.bin"
    pts.tofile(pc)
    rec = {
        "sample_id": "h1",
        "point_cloud": str(pc),
        "reviewed": True,
        "failure_confidence": 0.95,
        "hazard_score": 2.0,
        "uncertainty": 1.5,
        "boxes": [[0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]],
        "labels": [0],
    }
    (hard / "h1.json").write_text(json.dumps(rec), encoding="utf-8")
    hard_ds = ReviewedHardCaseDataset(hard_cfg, split="train")

    mixed = CompositeTrainingDataset(
        base_ds,
        hard_ds,
        hard_case_ratio=1.0,
        oversample_dangerous_classes=True,
        dangerous_classes=[0, 1, 3, 4],
        dangerous_class_weight=3.0,
        seed=7,
    )
    sample = mixed[0]
    assert sample["dataset_source"] == "hard_case"
    comp = mixed.composition()
    assert comp["hard_case_ratio"] == 1.0
    assert comp["weighted_hard_pool_size"] >= 3
