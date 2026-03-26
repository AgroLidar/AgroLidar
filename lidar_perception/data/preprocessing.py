from __future__ import annotations

import math

import numpy as np
import torch


def crop_points(points: np.ndarray, point_cloud_range: list[float]) -> np.ndarray:
    x_min, y_min, z_min, x_max, y_max, z_max = point_cloud_range
    mask = (
        (points[:, 0] >= x_min)
        & (points[:, 0] <= x_max)
        & (points[:, 1] >= y_min)
        & (points[:, 1] <= y_max)
        & (points[:, 2] >= z_min)
        & (points[:, 2] <= z_max)
    )
    return points[mask]


class BEVVoxelizer:
    def __init__(self, point_cloud_range: list[float], grid_size: list[int]):
        self.point_cloud_range = point_cloud_range
        self.grid_size = grid_size
        x_min, y_min, _, x_max, y_max, _ = point_cloud_range
        self.x_step = (x_max - x_min) / grid_size[0]
        self.y_step = (y_max - y_min) / grid_size[1]

    def voxelize(self, points: np.ndarray) -> np.ndarray:
        points = crop_points(points, self.point_cloud_range)
        h, w = self.grid_size
        bev = np.zeros((6, h, w), dtype=np.float32)

        if points.size == 0:
            return bev

        x_min, y_min, z_min, _, _, z_max = self.point_cloud_range
        ix = np.clip(((points[:, 0] - x_min) / self.x_step).astype(np.int32), 0, h - 1)
        iy = np.clip(((points[:, 1] - y_min) / self.y_step).astype(np.int32), 0, w - 1)

        z_norm = (points[:, 2] - z_min) / max(z_max - z_min, 1e-6)
        intensity = points[:, 3] if points.shape[1] > 3 else np.ones(points.shape[0], dtype=np.float32)
        distance = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2)

        counts = np.zeros((h, w), dtype=np.float32)
        max_height = np.full((h, w), -np.inf, dtype=np.float32)
        intensity_sum = np.zeros((h, w), dtype=np.float32)
        distance_min = np.full((h, w), np.inf, dtype=np.float32)
        mean_x = np.zeros((h, w), dtype=np.float32)
        mean_y = np.zeros((h, w), dtype=np.float32)

        for idx, idy, zn, inten, dist, px, py in zip(ix, iy, z_norm, intensity, distance, points[:, 0], points[:, 1]):
            counts[idx, idy] += 1.0
            max_height[idx, idy] = max(max_height[idx, idy], zn)
            intensity_sum[idx, idy] += inten
            distance_min[idx, idy] = min(distance_min[idx, idy], dist)
            mean_x[idx, idy] += px
            mean_y[idx, idy] += py

        occupied = counts > 0
        bev[0] = np.log1p(counts) / math.log(64.0)
        bev[1] = np.where(occupied, max_height, 0.0)
        bev[2] = np.where(occupied, intensity_sum / np.maximum(counts, 1.0), 0.0)
        bev[3] = np.where(occupied, distance_min / 80.0, 0.0)
        bev[4] = np.where(occupied, mean_x / np.maximum(counts, 1.0) / 40.0, 0.0)
        bev[5] = np.where(occupied, mean_y / np.maximum(counts, 1.0) / 40.0, 0.0)
        return bev.astype(np.float32)

    def points_to_grid(self, xy: np.ndarray) -> np.ndarray:
        x_min, y_min, _, _, _, _ = self.point_cloud_range
        h, w = self.grid_size
        ix = np.clip(((xy[:, 0] - x_min) / self.x_step).astype(np.int32), 0, h - 1)
        iy = np.clip(((xy[:, 1] - y_min) / self.y_step).astype(np.int32), 0, w - 1)
        return np.stack([ix, iy], axis=1)

    def build_detection_targets(self, boxes: np.ndarray, labels: np.ndarray, num_classes: int) -> dict[str, torch.Tensor]:
        h, w = self.grid_size
        heatmap = np.zeros((num_classes, h, w), dtype=np.float32)
        offsets = np.zeros((2, h, w), dtype=np.float32)
        sizes = np.zeros((3, h, w), dtype=np.float32)
        yaw = np.zeros((2, h, w), dtype=np.float32)
        mask = np.zeros((1, h, w), dtype=np.float32)

        if boxes.size == 0:
            return {
                "heatmap": torch.from_numpy(heatmap),
                "offsets": torch.from_numpy(offsets),
                "sizes": torch.from_numpy(sizes),
                "yaw": torch.from_numpy(yaw),
                "mask": torch.from_numpy(mask),
            }

        centers = self.points_to_grid(boxes[:, :2])
        x_min, y_min, _, _, _, _ = self.point_cloud_range
        for center, box, label in zip(centers, boxes, labels):
            gx, gy = int(center[0]), int(center[1])
            frac_x = (box[0] - x_min) / self.x_step - gx
            frac_y = (box[1] - y_min) / self.y_step - gy
            heatmap[label, gx, gy] = 1.0
            offsets[:, gx, gy] = np.array([frac_x, frac_y], dtype=np.float32)
            sizes[:, gx, gy] = box[3:6]
            yaw[:, gx, gy] = np.array([np.sin(box[6]), np.cos(box[6])], dtype=np.float32)
            mask[:, gx, gy] = 1.0

        return {
            "heatmap": torch.from_numpy(heatmap),
            "offsets": torch.from_numpy(offsets),
            "sizes": torch.from_numpy(sizes),
            "yaw": torch.from_numpy(yaw),
            "mask": torch.from_numpy(mask),
        }

    def build_segmentation_target(self, points: np.ndarray, boxes: np.ndarray, labels: np.ndarray, num_classes: int) -> torch.Tensor:
        h, w = self.grid_size
        target = np.zeros((h, w), dtype=np.int64)
        if points.size > 0:
            grid = self.points_to_grid(points[:, :2])
            ground = points[:, 2] < -1.0
            target[grid[ground, 0], grid[ground, 1]] = 1
            obstacles = points[:, 2] > 0.8
            target[grid[obstacles, 0], grid[obstacles, 1]] = min(num_classes - 1, 5)

        for box, label in zip(boxes, labels):
            cx, cy, _, dx, dy, _, _ = box
            x0, x1 = cx - dx / 2.0, cx + dx / 2.0
            y0, y1 = cy - dy / 2.0, cy + dy / 2.0
            corners = np.array([[x0, y0], [x1, y1]], dtype=np.float32)
            idx = self.points_to_grid(corners)
            xs = sorted(idx[:, 0].tolist())
            ys = sorted(idx[:, 1].tolist())
            cls = min(label + 2, num_classes - 1)
            target[xs[0] : xs[1] + 1, ys[0] : ys[1] + 1] = cls
        return torch.from_numpy(target)

    def build_obstacle_targets(self, points: np.ndarray) -> dict[str, torch.Tensor]:
        h, w = self.grid_size
        occupancy = np.zeros((1, h, w), dtype=np.float32)
        distance = np.zeros((1, h, w), dtype=np.float32)
        if points.size == 0:
            return {"occupancy": torch.from_numpy(occupancy), "distance": torch.from_numpy(distance)}

        grid = self.points_to_grid(points[:, :2])
        distances = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2)
        best = np.full((h, w), np.inf, dtype=np.float32)
        for (gx, gy), dist in zip(grid, distances):
            occupancy[0, gx, gy] = 1.0
            best[gx, gy] = min(best[gx, gy], dist)
        distance[0] = np.where(np.isfinite(best), best / 80.0, 0.0)
        return {"occupancy": torch.from_numpy(occupancy), "distance": torch.from_numpy(distance)}
