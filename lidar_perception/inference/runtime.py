from __future__ import annotations

from pathlib import Path

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

    def reset_tracking(self) -> None:
        self.predictor.reset_tracking()

    def infer_points(self, points):
        return self.predictor.infer(points)

    def infer_file(self, point_cloud_path: str):
        from lidar_perception.data.io import load_point_cloud

        if not Path(point_cloud_path).exists():
            raise FileNotFoundError(point_cloud_path)
        return self.infer_points(load_point_cloud(point_cloud_path))
