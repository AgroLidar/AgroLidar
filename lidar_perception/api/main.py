from __future__ import annotations

from pathlib import Path
from threading import Lock

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lidar_perception.inference.runtime import InferenceRuntime


class InferenceRequest(BaseModel):
    point_cloud_path: str
    config_path: str = "configs/base.yaml"
    checkpoint_path: str = "outputs/checkpoints/best.pt"
    reset_tracking: bool = False
    vehicle_speed_mps: float | None = None


app = FastAPI(title="AgroLidar API", version="0.1.0")
_runtime_cache: dict[tuple[str, str], InferenceRuntime] = {}
_runtime_lock = Lock()


def _get_runtime(config_path: str, checkpoint_path: str) -> InferenceRuntime:
    key = (config_path, checkpoint_path)
    with _runtime_lock:
        runtime = _runtime_cache.get(key)
        if runtime is None:
            runtime = InferenceRuntime(config_path=config_path, checkpoint_path=checkpoint_path)
            _runtime_cache[key] = runtime
        return runtime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "cached_runtimes": str(len(_runtime_cache))}


@app.post("/tracking/reset")
def reset_tracking(config_path: str = "configs/base.yaml", checkpoint_path: str = "outputs/checkpoints/best.pt") -> dict[str, str]:
    runtime = _get_runtime(config_path, checkpoint_path)
    runtime.reset_tracking()
    return {"status": "tracking_reset"}


@app.post("/predict")
def predict(request: InferenceRequest) -> dict:
    if not Path(request.point_cloud_path).exists():
        raise HTTPException(status_code=404, detail="Point cloud file not found")
    runtime = _get_runtime(request.config_path, request.checkpoint_path)
    if request.reset_tracking:
        runtime.reset_tracking()
    result = runtime.infer_file(request.point_cloud_path, vehicle_speed_mps=request.vehicle_speed_mps)
    return {
        "detections": [
            {
                "label": int(item["label"]),
                "label_name": str(item["label_name"]),
                "score": float(item["score"]),
                "box": np.asarray(item["box"]).tolist(),
                "distance_m": float(item["distance_m"]),
                "relative_position": item["relative_position"],
                "hazard_score": float(item["hazard_score"]),
                "risk_level": str(item["risk_level"]),
                "track_id": int(item["track_id"]),
                "track_status": str(item["track_status"]),
                "velocity_mps": item["velocity_mps"],
                "closing_speed_mps": float(item["closing_speed_mps"]),
                "time_to_collision_s": float(item["time_to_collision_s"]),
                "in_stop_zone": bool(item["in_stop_zone"]),
            }
            for item in result["detections"]
        ],
        "nearest_obstacle_distance_m": float(result["nearest_obstacle_distance_m"]),
        "scene_hazard_score": float(result["scene_hazard_score"]),
        "scene_risk_level": str(result["scene_risk_level"]),
        "preprocessing": result["preprocessing"],
        "vehicle_speed_mps": float(result["vehicle_speed_mps"]),
        "stopping_distance_m": float(result["stopping_distance_m"]),
        "stop_zone": result["stop_zone"],
        "min_time_to_collision_s": float(result["min_time_to_collision_s"]),
        "occupancy_fusion": result["occupancy_fusion"],
    }
