from __future__ import annotations
from pathlib import Path
from threading import Lock
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from lidar_perception.data.datasets import build_dataset
from lidar_perception.inference.runtime import InferenceRuntime
from lidar_perception.utils.config import load_config


class InferenceRequest(BaseModel):
    point_cloud_path: str
    config_path: str = "configs/base.yaml"
    checkpoint_path: str = "outputs/checkpoints/best.pt"
    reset_tracking: bool = False
    vehicle_speed_mps: Optional[float] = None


class DemoFrameRequest(BaseModel):
    config_path: str = "configs/demo_quick.yaml"
    checkpoint_path: str = "demo_outputs/checkpoints/best.pt"
    vehicle_speed_mps: float = 3.5
    reset_sequence: bool = False
    point_limit: int = 1600


app = FastAPI(title="AgroLidar API", version="0.1.0")
_runtime_cache: dict[tuple[str, str], InferenceRuntime] = {}
_runtime_lock = Lock()
_demo_sessions: dict[tuple[str, str], "DemoSession"] = {}
_demo_lock = Lock()


class DemoSession:
    def __init__(self, config_path: str, checkpoint_path: str):
        self.config_path = config_path
        self.checkpoint_path = checkpoint_path
        self.config = load_config(config_path)
        self.runtime = _get_runtime(config_path, checkpoint_path)
        self.dataset = build_dataset(self.config["data"], split="test")
        self.frame_index = 0

    def reset(self) -> None:
        self.runtime.reset_tracking()
        self.dataset = build_dataset(self.config["data"], split="test")
        self.frame_index = 0

    def next_frame(self, vehicle_speed_mps: float) -> tuple[dict, dict]:
        sample = self.dataset[self.frame_index % len(self.dataset)]
        result = self.runtime.infer_points(
            sample["points"].numpy(), vehicle_speed_mps=vehicle_speed_mps
        )
        meta = {
            "frame_index": self.frame_index,
            "point_cloud_range": self.config["data"]["point_cloud_range"],
            "class_names": self.config["data"]["class_names"],
        }
        self.frame_index += 1
        return result, meta


def _get_runtime(config_path: str, checkpoint_path: str) -> InferenceRuntime:
    key = (config_path, checkpoint_path)
    with _runtime_lock:
        runtime = _runtime_cache.get(key)
        if runtime is None:
            runtime = InferenceRuntime(config_path=config_path, checkpoint_path=checkpoint_path)
            _runtime_cache[key] = runtime
        return runtime


def _get_demo_session(config_path: str, checkpoint_path: str) -> DemoSession:
    key = (config_path, checkpoint_path)
    with _demo_lock:
        session = _demo_sessions.get(key)
        if session is None:
            session = DemoSession(config_path=config_path, checkpoint_path=checkpoint_path)
            _demo_sessions[key] = session
        return session


def _sample_points(points: np.ndarray, limit: int) -> list[list[float]]:
    if points.size == 0:
        return []
    if points.shape[0] > limit:
        step = max(points.shape[0] // limit, 1)
        points = points[::step][:limit]
    return points[:, :3].astype(float).tolist()


def _serialize_result(result: dict, meta: dict, point_limit: int) -> dict:
    return {
        "frame_index": int(meta["frame_index"]),
        "point_cloud_range": meta["point_cloud_range"],
        "class_names": meta["class_names"],
        "raw_points": _sample_points(
            result.get("filtered_points", np.empty((0, 3), dtype=np.float32)), point_limit
        ),
        "filtered_points": _sample_points(result["filtered_points"], point_limit),
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "cached_runtimes": str(len(_runtime_cache))}


@app.get("/", response_class=HTMLResponse)
def demo_page() -> HTMLResponse:
    html_path = Path(__file__).with_name("static").joinpath("demo.html")
    if not html_path.exists():
        raise HTTPException(status_code=500, detail="Demo HTML not found")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/tracking/reset")
def reset_tracking(
    config_path: str = "configs/base.yaml", checkpoint_path: str = "outputs/checkpoints/best.pt"
) -> dict[str, str]:
    runtime = _get_runtime(config_path, checkpoint_path)
    runtime.reset_tracking()
    return {"status": "tracking_reset"}


@app.post("/demo/api/reset")
def demo_reset(request: DemoFrameRequest) -> dict:
    session = _get_demo_session(request.config_path, request.checkpoint_path)
    session.reset()
    result, meta = session.next_frame(vehicle_speed_mps=request.vehicle_speed_mps)
    return _serialize_result(result, meta, point_limit=request.point_limit)


@app.post("/demo/api/frame")
def demo_frame(request: DemoFrameRequest) -> dict:
    session = _get_demo_session(request.config_path, request.checkpoint_path)
    if request.reset_sequence:
        session.reset()
    result, meta = session.next_frame(vehicle_speed_mps=request.vehicle_speed_mps)
    return _serialize_result(result, meta, point_limit=request.point_limit)


@app.post("/predict")
def predict(request: InferenceRequest) -> dict:
    if not Path(request.point_cloud_path).exists():
        raise HTTPException(status_code=404, detail="Point cloud file not found")
    runtime = _get_runtime(request.config_path, request.checkpoint_path)
    if request.reset_tracking:
        runtime.reset_tracking()
    result = runtime.infer_file(
        request.point_cloud_path, vehicle_speed_mps=request.vehicle_speed_mps
    )
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
