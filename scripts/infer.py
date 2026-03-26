from __future__ import annotations

import argparse
from pathlib import Path

from lidar_perception.data.datasets import build_dataset
from lidar_perception.data.io import load_point_cloud
from lidar_perception.inference.runtime import InferenceRuntime
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
    parser.add_argument("--sequence-length", type=int, default=1)
    parser.add_argument("--tractor-speed-mps", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    runtime = InferenceRuntime(args.config, args.checkpoint)

    if args.point_cloud:
        points_sequence = [load_point_cloud(args.point_cloud)]
        sources = [Path(args.point_cloud).name]
    else:
        dataset = build_dataset(config["data"], split="test")
        points_sequence = []
        sources = []
        for offset in range(args.sequence_length):
            sample_index = min(args.sample_index + offset, len(dataset) - 1)
            sample = dataset[sample_index]
            points_sequence.append(sample["points"].numpy())
            sources.append(f"synthetic_{sample_index}")

    for index, (source, points) in enumerate(zip(sources, points_sequence)):
        result = runtime.infer_points(points, vehicle_speed_mps=args.tractor_speed_mps)
        print(f"source={source}")
        print(f"nearest_obstacle_distance_m={result['nearest_obstacle_distance_m']:.2f}")
        print(f"scene_risk_level={result['scene_risk_level']}")
        print(
            f"vehicle_speed_mps={result['vehicle_speed_mps']:.2f} "
            f"stopping_distance_m={result['stopping_distance_m']:.2f} "
            f"stop_zone_occupied={result['stop_zone']['occupied']} "
            f"min_ttc_s={result['min_time_to_collision_s']:.2f}"
        )
        print(
            f"occupancy_fusion=history_size={result['occupancy_fusion']['history_size']} "
            f"window={result['occupancy_fusion']['window']} "
            f"decay={result['occupancy_fusion']['decay']:.2f}"
        )
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
                f"track_id={det['track_id']} track_status={det['track_status']} "
                f"velocity=({det['velocity_mps']['forward_mps']:.2f},{det['velocity_mps']['lateral_mps']:.2f})mps "
                f"in_stop_zone={det['in_stop_zone']} ttc_s={det['time_to_collision_s']:.2f} "
                f"center=({det['box'][0]:.2f}, {det['box'][1]:.2f}) "
                f"size=({det['box'][3]:.2f}, {det['box'][4]:.2f}, {det['box'][5]:.2f}) "
                f"distance_m={det['distance_m']:.2f} hazard={det['hazard_score']:.3f}"
            )

        if args.use_open3d and index == len(points_sequence) - 1:
            visualize_open3d(points, result["detections"], filtered_points=result["filtered_points"])
        elif not args.use_open3d:
            suffix = f"{source}_{index}" if len(points_sequence) > 1 else source
            save_path = args.save_path or Path(config["visualization"]["save_dir"]) / f"{suffix}.png"
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
