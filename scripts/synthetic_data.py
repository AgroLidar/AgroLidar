"""Generate synthetic LiDAR datasets for training augmentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic point-cloud scenes")
    parser.add_argument("--num-scenes", type=int, default=10)
    parser.add_argument("--sensor-types", nargs="+", default=["lidar"])
    parser.add_argument("--out-dir", default="data/synthetic")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    points_dir = out_dir / "points"
    labels_dir = out_dir / "labels"
    points_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Integrate Isaac Sim scene API once simulator contracts are finalized.
    # TODO: Integrate SKY ENGINE AI synthetic scenario generator.
    for idx in range(args.num_scenes):
        points = np.random.uniform(-30.0, 30.0, size=(4096, 4)).astype(np.float32)
        np.save(points_dir / f"scene_{idx:05d}.npy", points)
        label = {
            "scene_id": idx,
            "sensor_types": args.sensor_types,
            "objects": [
                {"class_name": "human", "x": 1.2, "y": 3.4, "z": 0.0},
                {"class_name": "vehicle", "x": -4.1, "y": 12.0, "z": 0.0},
            ],
        }
        (labels_dir / f"scene_{idx:05d}.json").write_text(json.dumps(label, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
