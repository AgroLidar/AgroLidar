from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from lidar_perception.data.datasets import build_dataset
from lidar_perception.data.io import load_point_cloud
from lidar_perception.inference.runtime import InferenceRuntime
from lidar_perception.utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LiDAR inference")
    parser.add_argument("--config", default="configs/infer.yaml")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--point-cloud", default=None)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--sequence-length", type=int, default=None)
    parser.add_argument("--tractor-speed-mps", type=float, default=None)
    parser.add_argument("--save-json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    runtime = InferenceRuntime(args.config, args.checkpoint)
    seq_len = args.sequence_length or int(config.get("inference", {}).get("sequence_length", 1))

    if args.point_cloud:
        points_sequence = [load_point_cloud(args.point_cloud)]
        sources = [Path(args.point_cloud).name]
    else:
        dataset = build_dataset(config["data"], split="test")
        points_sequence = []
        sources = []
        for offset in range(seq_len):
            sample_index = min(args.sample_index + offset, len(dataset) - 1)
            sample = dataset[sample_index]
            points_sequence.append(sample["points"].numpy())
            sources.append(f"synthetic_{sample_index}")

    save_dir = Path(config.get("inference", {}).get("save_predictions_dir", "outputs/predictions"))
    save_dir.mkdir(parents=True, exist_ok=True)

    for index, (source, points) in enumerate(zip(sources, points_sequence)):
        result = runtime.infer_points(points, vehicle_speed_mps=args.tractor_speed_mps)
        print(
            f"source={source} risk={result['scene_risk_level']} nearest_distance={result['nearest_obstacle_distance_m']:.2f}m"
        )
        if args.save_json:
            out = save_dir / f"{source}_{index}.json"
            out.write_text(
                json.dumps(
                    result, indent=2, default=lambda x: x.tolist() if hasattr(x, "tolist") else x
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
