from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from lidar_perception.data.preprocessing import BEVVoxelizer


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
            radius = max(candidate["box"][3], candidate["box"][4], existing["box"][3], existing["box"][4])
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
        self.voxelizer = BEVVoxelizer(config["data"]["point_cloud_range"], config["data"]["grid_size"])
        self.class_names = config["data"]["class_names"]
        self.hazard_weights = config["data"].get("hazard_weights", {})

    def preprocess(self, points: np.ndarray) -> torch.Tensor:
        bev = self.voxelizer.voxelize(points)
        return torch.from_numpy(bev).unsqueeze(0).to(self.device)

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
            ys, xs = np.where(heatmap[cls_idx] * confidence >= self.config["model"]["score_threshold"])
            for gx, gy in zip(ys, xs):
                center_x = x_min + (gx + offsets[0, gx, gy]) * x_step
                center_y = y_min + (gy + offsets[1, gx, gy]) * y_step
                size = np.maximum(sizes[:, gx, gy], 0.1)
                angle = float(np.arctan2(yaw[0, gx, gy], yaw[1, gx, gy]))
                score = float(heatmap[cls_idx, gx, gy] * confidence[gx, gy])
                box = np.array([center_x, center_y, 0.0, size[0], size[1], size[2], angle], dtype=np.float32)
                distance = float(np.linalg.norm(box[:2]))
                label_name = self.class_names[cls_idx]
                predictions.append(
                    {
                        "label": cls_idx,
                        "label_name": label_name,
                        "score": score,
                        "box": box,
                        "distance_m": distance,
                        "hazard_score": self.compute_hazard_score(label_name, score, distance),
                    }
                )

        predictions = circle_nms(predictions, self.config["model"]["nms_iou_threshold"])
        return predictions[: self.config["model"]["max_detections"]]

    def compute_hazard_score(self, class_name: str, confidence: float, distance_m: float) -> float:
        class_weight = float(self.hazard_weights.get(class_name, 0.5))
        distance_factor = max(0.1, 1.0 - min(distance_m, 50.0) / 50.0)
        return float(np.clip(class_weight * confidence * (0.6 + 0.4 * distance_factor), 0.0, 1.0))

    def infer(self, points: np.ndarray) -> dict:
        self.model.eval()
        with torch.no_grad():
            bev = self.preprocess(points)
            outputs = self.model(bev)
        detections = self.decode_detections(outputs)
        seg_logits = outputs["segmentation"][0].detach().cpu()
        obstacle = outputs["obstacle"]
        occupancy = torch.sigmoid(obstacle["occupancy"][0, 0]).detach().cpu()
        distance = torch.sigmoid(obstacle["distance"][0, 0]).detach().cpu() * 80.0
        nearest_distance = float(distance[occupancy > 0.5].min().item()) if (occupancy > 0.5).any() else float("inf")
        return {
            "detections": detections,
            "segmentation": seg_logits.argmax(dim=0).numpy(),
            "occupancy": occupancy.numpy(),
            "distance_map": distance.numpy(),
            "nearest_obstacle_distance_m": nearest_distance,
            "scene_hazard_score": float(max([item["hazard_score"] for item in detections], default=0.0)),
        }
