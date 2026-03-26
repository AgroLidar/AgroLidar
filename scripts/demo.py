from __future__ import annotations

import argparse
from pathlib import Path

from lidar_perception.data.datasets import build_dataset
from lidar_perception.inference.runtime import InferenceRuntime
from lidar_perception.utils.config import load_config
from lidar_perception.utils.visualization import visualize_bev


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run agricultural LiDAR MVP demo")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--num-scenes", type=int, default=3)
    parser.add_argument("--sequence-length", type=int, default=3)
    parser.add_argument("--tractor-speed-mps", type=float, default=3.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    runtime = InferenceRuntime(args.config, args.checkpoint)
    dataset = build_dataset(config["data"], split="test")
    output_dir = Path(config["visualization"]["save_dir"]) / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    for index in range(min(args.num_scenes, len(dataset))):
        runtime.reset_tracking()
        last_sample = None
        last_result = None
        for frame_offset in range(args.sequence_length):
            sample_index = min(index + frame_offset, len(dataset) - 1)
            sample = dataset[sample_index]
            last_sample = sample
            last_result = runtime.infer_points(sample["points"].numpy(), vehicle_speed_mps=args.tractor_speed_mps)
            print(
                f"scene={index} frame={frame_offset} detections={len(last_result['detections'])} "
                f"nearest_distance_m={last_result['nearest_obstacle_distance_m']:.2f} "
                f"scene_risk_level={last_result['scene_risk_level']} "
                f"stop_zone_occupied={last_result['stop_zone']['occupied']} "
                f"min_ttc_s={last_result['min_time_to_collision_s']:.2f}"
            )

        save_path = output_dir / f"scene_{index}.png"
        visualize_bev(
            last_sample["points"].numpy(),
            last_result["detections"],
            save_path=save_path,
            filtered_points=last_result["filtered_points"] if config["visualization"].get("show_filtered_points", True) else None,
            corridor_width_m=config["data"].get("preprocessing", {}).get("corridor_width_m"),
        )
        print(
            f"scene={index} final_hazard={last_result['scene_hazard_score']:.3f} "
            f"stopping_distance_m={last_result['stopping_distance_m']:.2f} "
            f"saved={save_path}"
        )


if __name__ == "__main__":
    main()
