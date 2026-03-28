"""Inference engine abstraction for synchronous model execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from lidar_perception.inference.runtime import InferenceRuntime


@dataclass
class InferenceResult:
    """Normalized inference output consumed by API schemas."""

    detections: list[dict[str, Any]]
    latency_ms: float


class InferenceEngine:
    """Facade that wraps ``InferenceRuntime`` for API-friendly inference calls."""

    def __init__(self, runtime: InferenceRuntime, model_path: str, model_version: str):
        """Initialize runtime facade.

        Args:
            runtime: Runtime instance with loaded model and preprocessing.
            model_path: Model checkpoint path used by this engine.
            model_version: Human-readable model version string.
        """
        self.runtime = runtime
        self.model_path = Path(model_path)
        self.model_version = model_version

    @classmethod
    def load_production(cls) -> "InferenceEngine":
        """Load production runtime from default paths.

        Returns:
            Ready-to-use inference engine.
        """
        config_path = "configs/infer.yaml"
        checkpoint_path = "outputs/checkpoints/best.pt"
        runtime = InferenceRuntime(config_path=config_path, checkpoint_path=checkpoint_path)
        return cls(runtime=runtime, model_path=checkpoint_path, model_version="production")

    def predict(self, points_np: np.ndarray, sensor_height_m: float = 1.5) -> InferenceResult:
        """Execute single-frame prediction.

        Args:
            points_np: Input point cloud in ``[N, 4]`` or ``[N, >=3]`` format.
            sensor_height_m: Sensor height in meters.

        Returns:
            Inference result containing detections and latency.
        """
        if points_np.ndim != 2 or points_np.shape[1] < 3:
            raise ValueError("Expected point cloud shape [N, >=3]")
        start = perf_counter()
        result = self.runtime.infer_points(points_np, vehicle_speed_mps=None)
        latency_ms = (perf_counter() - start) * 1000.0
        detections = []
        for detection in result.get("detections", []):
            detections.append(
                {
                    "class_name": str(detection.get("label_name", "unknown")),
                    "confidence": float(detection.get("score", 0.0)),
                    "distance_m": float(detection.get("distance_m", 0.0)),
                    "hazard_score": float(detection.get("hazard_score", 0.0)),
                    "bbox_3d": np.asarray(detection.get("box", np.zeros(7))).astype(float).tolist(),
                    "is_dangerous_class": str(detection.get("label_name", ""))
                    in {"human", "animal", "vehicle"},
                }
            )
        _ = sensor_height_m
        return InferenceResult(detections=detections, latency_ms=float(latency_ms))
