from __future__ import annotations

import argparse
from pathlib import Path

import torch

from lidar_perception.data.datasets import build_dataset
from lidar_perception.inference.predictor import Predictor
from lidar_perception.models.factory import build_model
from lidar_perception.utils.checkpoint import load_checkpoint
from lidar_perception.utils.config import load_config
from lidar_perception.utils.visualization import visualize_bev


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run agricultural LiDAR MVP demo")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--num-scenes", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    device = torch.device("cuda" if config.get("device") == "cuda" and torch.cuda.is_available() else "cpu")
    model = build_model(config["model"]).to(device)
    load_checkpoint(args.checkpoint, model, device=device)
    predictor = Predictor(model, config, device)
    dataset = build_dataset(config["data"], split="test")
    output_dir = Path(config["visualization"]["save_dir"]) / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    for index in range(min(args.num_scenes, len(dataset))):
        sample = dataset[index]
        result = predictor.infer(sample["points"].numpy())
        save_path = output_dir / f"scene_{index}.png"
        visualize_bev(sample["points"].numpy(), result["detections"], save_path=save_path)
        print(
            f"scene={index} detections={len(result['detections'])} "
            f"nearest_distance_m={result['nearest_obstacle_distance_m']:.2f} "
            f"scene_hazard_score={result['scene_hazard_score']:.3f} "
            f"saved={save_path}"
        )


if __name__ == "__main__":
    main()
