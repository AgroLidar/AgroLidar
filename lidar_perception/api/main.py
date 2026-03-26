from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lidar_perception.data.io import load_point_cloud
from lidar_perception.inference.predictor import Predictor
from lidar_perception.models.factory import build_model
from lidar_perception.utils.checkpoint import load_checkpoint
from lidar_perception.utils.config import load_config


class InferenceRequest(BaseModel):
    point_cloud_path: str
    config_path: str = "configs/base.yaml"
    checkpoint_path: str = "outputs/checkpoints/best.pt"


app = FastAPI(title="AgriLiDAR Guard API", version="0.1.0")


def _load_runtime(config_path: str, checkpoint_path: str):
    config = load_config(config_path)
    device = torch.device("cuda" if config.get("device") == "cuda" and torch.cuda.is_available() else "cpu")
    model = build_model(config["model"]).to(device)
    load_checkpoint(checkpoint_path, model, device=device)
    predictor = Predictor(model, config, device)
    return predictor


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(request: InferenceRequest) -> dict:
    if not Path(request.point_cloud_path).exists():
        raise HTTPException(status_code=404, detail="Point cloud file not found")
    predictor = _load_runtime(request.config_path, request.checkpoint_path)
    points = load_point_cloud(request.point_cloud_path)
    result = predictor.infer(points)
    return {
        "detections": [
            {
                "label": int(item["label"]),
                "score": float(item["score"]),
                "box": np.asarray(item["box"]).tolist(),
                "distance_m": float(np.linalg.norm(np.asarray(item["box"])[:2])),
                "hazard_score": float(item["hazard_score"]),
            }
            for item in result["detections"]
        ],
        "nearest_obstacle_distance_m": float(result["nearest_obstacle_distance_m"]),
        "scene_hazard_score": float(result["scene_hazard_score"]),
    }
