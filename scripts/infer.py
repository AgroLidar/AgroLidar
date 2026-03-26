from __future__ import annotations

import argparse
from pathlib import Path

import torch

from lidar_perception.data.datasets import build_dataset
from lidar_perception.data.io import load_point_cloud
from lidar_perception.models.factory import build_model
from lidar_perception.inference.predictor import Predictor
from lidar_perception.utils.checkpoint import load_checkpoint
from lidar_perception.utils.config import load_config
from lidar_perception.utils.visualization import visualize_bev, visualize_open3d


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LiDAR inference")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--point-cloud", default=None)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--save-path", default=None)
    parser.add_argument("--use-open3d", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    device = torch.device("cuda" if config.get("device") == "cuda" and torch.cuda.is_available() else "cpu")
    model = build_model(config["model"]).to(device)
    load_checkpoint(args.checkpoint, model, device=device)
    predictor = Predictor(model, config, device)

    if args.point_cloud:
        points = load_point_cloud(args.point_cloud)
        source = Path(args.point_cloud).name
    else:
        dataset = build_dataset(config["data"], split="test")
        sample = dataset[args.sample_index]
        points = sample["points"].numpy()
        source = f"synthetic_{args.sample_index}"

    result = predictor.infer(points)
    print(f"source={source}")
    print(f"nearest_obstacle_distance_m={result['nearest_obstacle_distance_m']:.2f}")
    print(f"scene_risk_level={result['scene_risk_level']}")
    print(
        "preprocessing="
        f"filtered_points={result['preprocessing']['filtered_point_count']} "
        f"original_points={result['preprocessing']['original_point_count']} "
        f"vegetation_ratio={result['preprocessing']['vegetation_ratio']:.3f} "
        f"terrain_variation_m={result['preprocessing']['terrain_variation_m']:.3f}"
    )
    for det in result["detections"][:10]:
        print(
            f"label={det['label_name']} score={det['score']:.3f} risk={det['risk_level']} "
            f"center=({det['box'][0]:.2f}, {det['box'][1]:.2f}) "
            f"size=({det['box'][3]:.2f}, {det['box'][4]:.2f}, {det['box'][5]:.2f}) "
            f"distance_m={det['distance_m']:.2f} hazard={det['hazard_score']:.3f}"
        )

    if args.use_open3d:
        visualize_open3d(points, result["detections"], filtered_points=result["filtered_points"])
    else:
        save_path = args.save_path or Path(config["visualization"]["save_dir"]) / f"{source}.png"
        visualize_bev(
            points,
            result["detections"],
            save_path=save_path,
            filtered_points=result["filtered_points"] if config["visualization"].get("show_filtered_points", True) else None,
            corridor_width_m=config["data"].get("preprocessing", {}).get("corridor_width_m"),
        )
        print(f"saved_visualization={save_path}")


if __name__ == "__main__":
    main()
