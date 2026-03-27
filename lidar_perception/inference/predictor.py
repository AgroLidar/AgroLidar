from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from lidar_perception.data.preprocessing import AgroPreprocessor, BEVVoxelizer
from lidar_perception.inference.tracker import TemporalDetectionTracker
from lidar_perception.risk.scoring import HazardScorer, RiskContext


@dataclass
class DetectionResult:
    label: int
    score: float
    box: np.ndarray


def circle_nms(predictions: list[dict], iou_threshold: float) -> list[dict]:
    kept = []
    for candidate in sorted(predictions, key=lambda item: item["score"], reverse=True):
        should_keep = True
        for existing in kept:
            dist = np.linalg.norm(candidate["box"][:2] - existing["box"][:2])
            radius = max(
                candidate["box"][3], candidate["box"][4], existing["box"][3], existing["box"][4]
            )
            if dist < iou_threshold * radius:
                should_keep = False
                break
        if should_keep:
            kept.append(candidate)
    return kept


class Predictor:
    def __init__(self, model: torch.nn.Module, config: dict, device: torch.device):
        self.model = model
        self.config = config
        self.device = device
        self.voxelizer = BEVVoxelizer(
            config["data"]["point_cloud_range"], config["data"]["grid_size"]
        )
        self.preprocessor = AgroPreprocessor(
            config["data"]["point_cloud_range"], config["data"].get("preprocessing", {})
        )
        self.class_names = config["data"]["class_names"]
        self.hazard_weights = config["data"].get("hazard_weights", {})
        self.hazard_scorer = HazardScorer(
            self.hazard_weights,
            corridor_width_m=float(
                config["data"].get("preprocessing", {}).get("corridor_width_m", 3.2)
            ),
        )
        preprocessing_config = config["data"].get("preprocessing", {})
        inference_config = config.get("inference", {})
        self.max_candidates_per_class = int(config["model"].get("max_candidates_per_class", 32))
        self.corridor_width_m = float(preprocessing_config.get("corridor_width_m", 3.2))
        self.emergency_distance_m = float(preprocessing_config.get("emergency_distance_m", 8.0))
        self.warning_distance_m = float(preprocessing_config.get("warning_distance_m", 18.0))
        tracker_config = dict(config["model"].get("temporal_tracking", {}))
        tracker_config.setdefault("frame_dt_s", inference_config.get("frame_dt_s", 0.2))
        self.tracker = TemporalDetectionTracker(tracker_config)

    def reset_tracking(self) -> None:
        self.tracker.reset()

    def preprocess(self, points: np.ndarray) -> tuple[torch.Tensor, np.ndarray, dict]:
        filtered_points, metadata = self.preprocessor.process(points)
        bev = self.voxelizer.voxelize(filtered_points)
        return (
            torch.from_numpy(bev).unsqueeze(0).to(self.device),
            filtered_points,
            {
                "filtered_point_count": metadata.filtered_point_count,
                "original_point_count": metadata.original_point_count,
                "vegetation_ratio": metadata.vegetation_ratio,
                "terrain_variation_m": metadata.terrain_variation_m,
            },
        )

    def decode_detections(self, outputs: dict[str, torch.Tensor]) -> list[dict]:
        det = outputs["detection"]
        heatmap = torch.sigmoid(det["heatmap"][0]).detach().cpu().numpy()
        confidence = torch.sigmoid(det["confidence"][0, 0]).detach().cpu().numpy()
        offsets = det["offsets"][0].detach().cpu().numpy()
        sizes = det["sizes"][0].detach().cpu().numpy()
        yaw = det["yaw"][0].detach().cpu().numpy()
        h, w = heatmap.shape[1:]
        x_min, y_min, _, _, _, _ = self.config["data"]["point_cloud_range"]
        x_step = (self.config["data"]["point_cloud_range"][3] - x_min) / h
        y_step = (self.config["data"]["point_cloud_range"][4] - y_min) / w

        predictions = []
        for cls_idx in range(heatmap.shape[0]):
            class_scores = heatmap[cls_idx] * confidence
            candidate_indices = np.argwhere(class_scores >= self.config["model"]["score_threshold"])
            if candidate_indices.shape[0] > self.max_candidates_per_class:
                candidate_scores = class_scores[candidate_indices[:, 0], candidate_indices[:, 1]]
                top_idx = np.argsort(candidate_scores)[-self.max_candidates_per_class :]
                candidate_indices = candidate_indices[top_idx]
            ys, xs = candidate_indices[:, 0], candidate_indices[:, 1]
            for gx, gy in zip(ys, xs):
                center_x = x_min + (gx + offsets[0, gx, gy]) * x_step
                center_y = y_min + (gy + offsets[1, gx, gy]) * y_step
                size = np.maximum(sizes[:, gx, gy], 0.1)
                angle = float(np.arctan2(yaw[0, gx, gy], yaw[1, gx, gy]))
                score = float(heatmap[cls_idx, gx, gy] * confidence[gx, gy])
                box = np.array(
                    [center_x, center_y, 0.0, size[0], size[1], size[2], angle], dtype=np.float32
                )
                distance = float(np.linalg.norm(box[:2]))
                label_name = self.class_names[cls_idx]
                relative_position = {"forward_m": float(center_x), "lateral_m": float(center_y)}
                predictions.append(
                    {
                        "label": cls_idx,
                        "label_name": label_name,
                        "score": score,
                        "box": box,
                        "distance_m": distance,
                        "relative_position": relative_position,
                        "hazard_score": self.compute_hazard_score(
                            label_name, score, distance, relative_position
                        ),
                    }
                )

        predictions = circle_nms(predictions, self.config["model"]["nms_iou_threshold"])
        return predictions[: self.config["model"]["max_detections"]]

    def compute_hazard_score(
        self,
        class_name: str,
        confidence: float,
        distance_m: float,
        relative_position: dict[str, float],
    ) -> float:
        return self.hazard_scorer.score(
            RiskContext(
                class_name=class_name,
                confidence=confidence,
                distance_m=distance_m,
                forward_m=relative_position["forward_m"],
                lateral_m=relative_position["lateral_m"],
                track_consistency=0.8,
                vehicle_speed_mps=float(
                    self.config.get("inference", {}).get("default_vehicle_speed_mps", 3.0)
                ),
            )
        )

    def compute_risk_level(
        self, distance_m: float, hazard_score: float, relative_position: dict[str, float]
    ) -> str:
        return self.hazard_scorer.risk_level(hazard_score, distance_m)

    def infer(self, points: np.ndarray) -> dict:
        self.model.eval()
        with torch.no_grad():
            bev, filtered_points, preprocessing_metadata = self.preprocess(points)
            outputs = self.model(bev)
        detections = self.decode_detections(outputs)
        for detection in detections:
            detection["risk_level"] = self.compute_risk_level(
                detection["distance_m"],
                detection["hazard_score"],
                detection["relative_position"],
            )
        detections = self.tracker.update(detections)
        seg_logits = outputs["segmentation"][0].detach().cpu()
        obstacle = outputs["obstacle"]
        occupancy = torch.sigmoid(obstacle["occupancy"][0, 0]).detach().cpu()
        distance = torch.sigmoid(obstacle["distance"][0, 0]).detach().cpu() * 80.0
        nearest_distance = (
            float(distance[occupancy > 0.5].min().item())
            if (occupancy > 0.5).any()
            else float("inf")
        )
        return {
            "detections": detections,
            "filtered_points": filtered_points,
            "segmentation": seg_logits.argmax(dim=0).numpy(),
            "occupancy": occupancy.numpy(),
            "distance_map": distance.numpy(),
            "nearest_obstacle_distance_m": nearest_distance,
            "scene_hazard_score": float(
                max([item["hazard_score"] for item in detections], default=0.0)
            ),
            "scene_risk_level": "emergency"
            if any(item["risk_level"] == "emergency" for item in detections)
            else (
                "warning"
                if any(item["risk_level"] == "warning" for item in detections)
                else "monitor"
            ),
            "preprocessing": preprocessing_metadata,
        }
