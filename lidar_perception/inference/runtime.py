from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
import torch

from lidar_perception.inference.predictor import Predictor
from lidar_perception.models.factory import build_model
from lidar_perception.utils.checkpoint import load_checkpoint
from lidar_perception.utils.config import load_config


class InferenceRuntime:
    """Persistent runtime that keeps model and temporal tracking alive across requests."""

    def __init__(self, config_path: str, checkpoint_path: str):
        self.config_path = str(config_path)
        self.checkpoint_path = str(checkpoint_path)
        self.config = load_config(config_path)
        self.device = torch.device("cuda" if self.config.get("device") == "cuda" and torch.cuda.is_available() else "cpu")
        self.model = build_model(self.config["model"]).to(self.device)
        load_checkpoint(self.checkpoint_path, self.model, device=self.device)
        self.predictor = Predictor(self.model, self.config, self.device)
        inference_config = self.config.get("inference", {})
        self.frame_dt_s = float(inference_config.get("frame_dt_s", 0.2))
        self.default_vehicle_speed_mps = float(inference_config.get("default_vehicle_speed_mps", 3.0))
        self.braking_deceleration_mps2 = float(inference_config.get("braking_deceleration_mps2", 2.5))
        self.reaction_time_s = float(inference_config.get("reaction_time_s", 0.5))
        self.safety_margin_m = float(inference_config.get("safety_margin_m", 1.5))
        self.stop_zone_width_m = float(inference_config.get("stop_zone_width_m", 3.2))
        self.occupancy_fusion_window = int(inference_config.get("occupancy_fusion_window", 5))
        self.occupancy_fusion_decay = float(inference_config.get("occupancy_fusion_decay", 0.72))
        self._occupancy_history: deque[np.ndarray] = deque(maxlen=self.occupancy_fusion_window)
        self._distance_history: deque[np.ndarray] = deque(maxlen=self.occupancy_fusion_window)

    def reset_tracking(self) -> None:
        self.predictor.reset_tracking()
        self._occupancy_history.clear()
        self._distance_history.clear()

    def _fuse_maps(self, occupancy: np.ndarray, distance_map: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        self._occupancy_history.append(occupancy.copy())
        self._distance_history.append(distance_map.copy())
        weights = np.array(
            [self.occupancy_fusion_decay ** idx for idx in range(len(self._occupancy_history) - 1, -1, -1)],
            dtype=np.float32,
        )
        weights /= np.maximum(weights.sum(), 1e-6)
        fused_occupancy = np.zeros_like(occupancy, dtype=np.float32)
        fused_distance = np.zeros_like(distance_map, dtype=np.float32)
        weight_sum = np.zeros_like(distance_map, dtype=np.float32)

        for weight, occ, dist in zip(weights, self._occupancy_history, self._distance_history):
            fused_occupancy += weight * occ
            valid = occ > 0.5
            fused_distance[valid] += weight * dist[valid]
            weight_sum[valid] += weight

        fused_distance = np.where(weight_sum > 0.0, fused_distance / np.maximum(weight_sum, 1e-6), 0.0)
        return fused_occupancy, fused_distance

    def _compute_stopping_distance(self, vehicle_speed_mps: float) -> float:
        reaction_distance = vehicle_speed_mps * self.reaction_time_s
        braking_distance = (vehicle_speed_mps ** 2) / max(2.0 * self.braking_deceleration_mps2, 1e-6)
        return reaction_distance + braking_distance + self.safety_margin_m

    def _annotate_stop_zone(self, result: dict, vehicle_speed_mps: float) -> dict:
        stopping_distance_m = self._compute_stopping_distance(vehicle_speed_mps)
        stop_zone_occupied = False
        min_ttc_s = float("inf")
        for detection in result["detections"]:
            in_stop_zone = (
                detection["relative_position"]["forward_m"] >= 0.0
                and detection["relative_position"]["forward_m"] <= stopping_distance_m
                and abs(detection["relative_position"]["lateral_m"]) <= self.stop_zone_width_m / 2.0
            )
            closing_speed = max(vehicle_speed_mps - detection["velocity_mps"]["forward_mps"], 0.0)
            ttc_s = detection["distance_m"] / max(closing_speed, 1e-6) if closing_speed > 1e-3 else float("inf")
            detection["closing_speed_mps"] = float(closing_speed)
            detection["time_to_collision_s"] = float(ttc_s) if np.isfinite(ttc_s) else float("inf")
            detection["in_stop_zone"] = bool(in_stop_zone)
            if in_stop_zone:
                stop_zone_occupied = True
            if np.isfinite(ttc_s):
                min_ttc_s = min(min_ttc_s, float(ttc_s))

        result["vehicle_speed_mps"] = float(vehicle_speed_mps)
        result["stopping_distance_m"] = float(stopping_distance_m)
        result["stop_zone"] = {
            "width_m": float(self.stop_zone_width_m),
            "length_m": float(stopping_distance_m),
            "occupied": bool(stop_zone_occupied),
        }
        result["min_time_to_collision_s"] = float(min_ttc_s) if np.isfinite(min_ttc_s) else float("inf")
        if stop_zone_occupied:
            result["scene_risk_level"] = "emergency"
        return result

    def infer_points(self, points, vehicle_speed_mps: float | None = None):
        result = self.predictor.infer(points)
        fused_occupancy, fused_distance = self._fuse_maps(result["occupancy"], result["distance_map"])
        result["raw_occupancy"] = result["occupancy"]
        result["raw_distance_map"] = result["distance_map"]
        result["occupancy"] = fused_occupancy
        result["distance_map"] = fused_distance
        occupied = fused_occupancy > 0.5
        result["nearest_obstacle_distance_m"] = float(fused_distance[occupied].min()) if occupied.any() else float("inf")
        result["occupancy_fusion"] = {
            "history_size": len(self._occupancy_history),
            "window": self.occupancy_fusion_window,
            "decay": self.occupancy_fusion_decay,
        }
        speed = self.default_vehicle_speed_mps if vehicle_speed_mps is None else float(vehicle_speed_mps)
        return self._annotate_stop_zone(result, speed)

    def infer_file(self, point_cloud_path: str, vehicle_speed_mps: float | None = None):
        from lidar_perception.data.io import load_point_cloud

        if not Path(point_cloud_path).exists():
            raise FileNotFoundError(point_cloud_path)
        return self.infer_points(load_point_cloud(point_cloud_path), vehicle_speed_mps=vehicle_speed_mps)
