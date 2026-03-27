from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AugmentationConfig:
    enabled: bool = True
    rotation_deg: float = 10.0
    scale_range: tuple[float, float] = (0.95, 1.05)
    translation_std: float = 0.2
    dropout_ratio: float = 0.02
    intensity_noise_std: float = 0.05
    weather_attenuation_prob: float = 0.3
    weather_attenuation_strength: float = 0.2
    occlusion_prob: float = 0.2
    terrain_jitter_std: float = 0.03


class PointCloudAugmentor:
    def __init__(self, config: dict):
        self.config = AugmentationConfig(
            enabled=config.get("enabled", True),
            rotation_deg=float(config.get("rotation_deg", 10.0)),
            scale_range=tuple(config.get("scale_range", [0.95, 1.05])),
            translation_std=float(config.get("translation_std", 0.2)),
            dropout_ratio=float(config.get("dropout_ratio", 0.02)),
            intensity_noise_std=float(config.get("intensity_noise_std", 0.05)),
            weather_attenuation_prob=float(config.get("weather_attenuation_prob", 0.3)),
            weather_attenuation_strength=float(config.get("weather_attenuation_strength", 0.2)),
            occlusion_prob=float(config.get("occlusion_prob", 0.2)),
            terrain_jitter_std=float(config.get("terrain_jitter_std", 0.03)),
        )

    def __call__(
        self, points: np.ndarray, boxes: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray | None]:
        if not self.config.enabled:
            return points, boxes

        augmented = points.copy()
        transformed_boxes = boxes.copy() if boxes is not None else None

        angle = np.deg2rad(np.random.uniform(-self.config.rotation_deg, self.config.rotation_deg))
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        rotation = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float32)
        augmented[:, :2] = augmented[:, :2] @ rotation.T

        scale = np.random.uniform(self.config.scale_range[0], self.config.scale_range[1])
        augmented[:, :3] *= scale

        translation = np.random.normal(0.0, self.config.translation_std, size=(1, 3)).astype(
            np.float32
        )
        augmented[:, :3] += translation
        augmented[:, 2] += np.random.normal(
            0.0, self.config.terrain_jitter_std, size=(augmented.shape[0],)
        ).astype(np.float32)

        if augmented.shape[1] > 3:
            augmented[:, 3] += np.random.normal(
                0.0, self.config.intensity_noise_std, size=(augmented.shape[0],)
            ).astype(np.float32)
            augmented[:, 3] = np.clip(augmented[:, 3], 0.0, 1.0)

        if np.random.rand() < self.config.weather_attenuation_prob:
            distances = np.linalg.norm(augmented[:, :2], axis=1)
            keep_probability = np.exp(-self.config.weather_attenuation_strength * distances / 40.0)
            weather_mask = np.random.rand(augmented.shape[0]) < keep_probability
            augmented = augmented[weather_mask]

        if np.random.rand() < self.config.occlusion_prob and augmented.shape[0] > 0:
            axis = np.random.choice([0, 1])
            threshold = np.quantile(augmented[:, axis], np.random.uniform(0.25, 0.75))
            side = np.random.choice([-1, 1])
            occlusion_mask = augmented[:, axis] * side <= threshold * side
            augmented = augmented[occlusion_mask]

        keep_mask = np.random.rand(augmented.shape[0]) > self.config.dropout_ratio
        augmented = augmented[keep_mask]

        if transformed_boxes is not None and transformed_boxes.size > 0:
            transformed_boxes[:, :2] = transformed_boxes[:, :2] @ rotation.T
            transformed_boxes[:, :3] *= scale
            transformed_boxes[:, :3] += translation
            transformed_boxes[:, 6] += angle

        return augmented, transformed_boxes
