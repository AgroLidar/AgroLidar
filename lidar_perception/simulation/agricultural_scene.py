from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AgriculturalObject:
    class_id: int
    name: str
    size: tuple[float, float, float]
    z_center: float
    min_points: int
    max_points: int


DEFAULT_OBJECTS = {
    "human": AgriculturalObject(0, "human", (0.8, 0.8, 1.8), 0.3, 80, 180),
    "animal": AgriculturalObject(1, "animal", (1.2, 0.8, 1.2), 0.1, 90, 220),
    "vehicle": AgriculturalObject(2, "vehicle", (4.5, 2.2, 2.2), 0.6, 250, 650),
    "post": AgriculturalObject(3, "post", (0.3, 0.3, 1.8), 0.4, 50, 120),
    "rock": AgriculturalObject(4, "rock", (0.9, 0.9, 0.8), -0.2, 60, 160),
}


class AgriculturalSceneGenerator:
    """Synthetic field scenes intentionally avoid urban priors like flat roads or lane layouts."""

    def __init__(self, config: dict, rng: np.random.Generator):
        self.config = config
        self.rng = rng
        self.pc_range = config["point_cloud_range"]
        self.simulation = config.get("simulation", {})
        self.class_names = config["class_names"]

    def _terrain_height(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        variation = float(self.simulation.get("terrain_variation", 0.25))
        return (
            -1.7
            + variation * np.sin(0.08 * x)
            + 0.5 * variation * np.cos(0.12 * y)
            + 0.2 * variation * np.sin(0.05 * (x + y))
        ).astype(np.float32)

    def _sample_ground(self, count: int) -> np.ndarray:
        x_min, y_min, _, x_max, y_max, _ = self.pc_range
        x = self.rng.uniform(x_min, x_max, count).astype(np.float32)
        y = self.rng.uniform(y_min, y_max, count).astype(np.float32)
        z = self._terrain_height(x, y) + self.rng.normal(0.0, 0.04, count).astype(np.float32)
        intensity = self.rng.uniform(0.1, 0.6, count).astype(np.float32)
        return np.stack([x, y, z, intensity], axis=1)

    def _sample_vegetation(self, count: int) -> np.ndarray:
        x_min, y_min, _, x_max, y_max, _ = self.pc_range
        x = self.rng.uniform(x_min, x_max, count).astype(np.float32)
        y = self.rng.uniform(y_min, y_max, count).astype(np.float32)
        ground = self._terrain_height(x, y)
        height = self.rng.uniform(0.1, 1.3, count).astype(np.float32)
        z = ground + height
        intensity = self.rng.uniform(0.2, 0.9, count).astype(np.float32)
        return np.stack([x, y, z, intensity], axis=1)

    def _sample_air_noise(self, count: int) -> np.ndarray:
        x_min, y_min, z_min, x_max, y_max, z_max = self.pc_range
        xyz = np.stack(
            [
                self.rng.uniform(x_min, x_max, count),
                self.rng.uniform(y_min, y_max, count),
                self.rng.uniform(z_min, z_max, count),
            ],
            axis=1,
        ).astype(np.float32)
        intensity = self.rng.uniform(0.0, 0.3, size=(count, 1)).astype(np.float32)
        return np.concatenate([xyz, intensity], axis=1)

    def _sample_object_points(self, center: np.ndarray, size: tuple[float, float, float], yaw: float, count: int) -> np.ndarray:
        dx, dy, dz = size
        local = self.rng.uniform([-dx / 2, -dy / 2, -dz / 2], [dx / 2, dy / 2, dz / 2], size=(count, 3)).astype(np.float32)
        rotation = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]], dtype=np.float32)
        local[:, :2] = local[:, :2] @ rotation.T
        local[:, :3] += center[None, :]
        local[:, 2] += self._terrain_height(local[:, 0], local[:, 1])
        intensity = self.rng.uniform(0.45, 1.0, size=(count, 1)).astype(np.float32)
        return np.concatenate([local, intensity], axis=1)

    def generate(self, num_points: int, max_objects: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        vegetation_density = float(self.simulation.get("vegetation_density", 0.25))
        ground_count = int(num_points * 0.48)
        vegetation_count = int(num_points * vegetation_density)
        air_noise_count = int(num_points * 0.08)
        scene = [
            self._sample_ground(ground_count),
            self._sample_vegetation(vegetation_count),
            self._sample_air_noise(air_noise_count),
        ]

        boxes = []
        labels = []
        x_min, y_min, _, x_max, y_max, _ = self.pc_range
        num_objects = int(self.rng.integers(4, min(max_objects, 12)))

        for _ in range(num_objects):
            name = self.class_names[int(self.rng.integers(0, len(self.class_names)))]
            obj = DEFAULT_OBJECTS[name]
            center = np.array(
                [
                    self.rng.uniform(x_min + 8.0, x_max - 6.0),
                    self.rng.uniform(y_min + 2.0, y_max - 2.0),
                    obj.z_center,
                ],
                dtype=np.float32,
            )
            yaw = float(self.rng.uniform(-np.pi, np.pi))
            count = int(self.rng.integers(obj.min_points, obj.max_points))
            points = self._sample_object_points(center, obj.size, yaw, count)
            scene.append(points)
            boxes.append([center[0], center[1], center[2], *obj.size, yaw])
            labels.append(obj.class_id)

        points = np.concatenate(scene, axis=0).astype(np.float32)
        return points, np.asarray(boxes, dtype=np.float32), np.asarray(labels, dtype=np.int64)
