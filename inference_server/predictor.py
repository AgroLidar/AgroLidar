from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import torch
from numpy.typing import NDArray

from inference_server.models import Detection
from lidar_perception.models.factory import build_model
from lidar_perception.utils.checkpoint import load_checkpoint
from lidar_perception.utils.config import load_config

KNOWN_CLASSES = ["human", "animal", "rock", "post", "vehicle"]
KnownClassName = Literal["human", "animal", "rock", "post", "vehicle"]
RiskLevel = Literal["critical", "warning", "safe"]


class BEVPredictor:
    EXPECTED_SHAPE = (4, 512, 512)

    def __init__(
        self,
        checkpoint_path: str,
        config_path: str,
        device: str = "cpu",
        warmup_runs: int = 3,
        p95_latency_threshold_ms: float = 200.0,
        min_healthy_inferences: int = 10,
        backend: str = "pytorch",
        onnx_path: str = "outputs/onnx/model.onnx",
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.config_path = config_path
        self.device = torch.device(device)
        self.config = load_config(config_path)
        self.backend = backend.lower()
        self.onnx_path = onnx_path
        self.onnx_session: Any | None = None
        self.onnx_input_name: str | None = None
        self.onnx_output_names: list[str] = []

        self.model = None
        if self.backend == "pytorch":
            self.model = build_model(self.config["model"]).to(self.device)
            self.model.eval()

        self.model_loaded = False
        self.model_version = "unknown"
        self.model_loaded_at = time.time()

        self.total_inferences = 0
        self.failed_inferences = 0
        self._latencies_ms: deque[float] = deque(maxlen=1000)
        self._recent_success: deque[bool] = deque(maxlen=10)
        self.last_collision_risk = "none"
        self.p95_latency_threshold_ms = p95_latency_threshold_ms
        self.min_healthy_inferences = min_healthy_inferences

        self._load_model()
        self._load_model_version()
        self._warmup(max(0, int(warmup_runs)))

    @property
    def supported_classes(self) -> list[str]:
        return KNOWN_CLASSES

    @property
    def input_shape(self) -> tuple[int, int, int]:
        return self.EXPECTED_SHAPE

    @property
    def last_latency_ms(self) -> float:
        return self._latencies_ms[-1] if self._latencies_ms else 0.0

    def _load_model(self) -> None:
        if self.backend == "pytorch":
            if self.model is None:
                raise RuntimeError("PyTorch model is not initialized")
            load_checkpoint(self.checkpoint_path, self.model, device=self.device)
            self.model_loaded = True
            return

        if self.backend == "onnx":
            import onnxruntime as ort

            providers: list[str] = ["CPUExecutionProvider"]
            if "CUDAExecutionProvider" in ort.get_available_providers():
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self.onnx_session = ort.InferenceSession(self.onnx_path, providers=providers)
            self.onnx_input_name = self.onnx_session.get_inputs()[0].name
            self.onnx_output_names = [output.name for output in self.onnx_session.get_outputs()]
            self.model_loaded = True
            return

        raise ValueError(f"Unsupported backend: {self.backend}")

    def _load_model_version(self) -> None:
        registry_path = Path("outputs/registry/registry.json")
        if not registry_path.exists():
            return
        try:
            entries = json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(entries, list) or not entries:
            return
        sorted_entries = sorted(entries, key=lambda item: str(item.get("timestamp", "")))
        production = [item for item in sorted_entries if item.get("status") == "production"]
        target = production[-1] if production else sorted_entries[-1]
        self.model_version = str(target.get("version", "unknown"))

    def _warmup(self, warmup_runs: int) -> None:
        if not self.model_loaded:
            return
        warmup_input = np.zeros(self.EXPECTED_SHAPE, dtype=np.float32)
        for _ in range(warmup_runs):
            try:
                self.predict(warmup_input)
            except Exception:
                self._recent_success.append(False)

    def _validate_frame(self, frame_array: NDArray[np.float32]) -> NDArray[np.float32]:
        if frame_array.shape != self.EXPECTED_SHAPE:
            raise ValueError(f"Invalid frame shape {frame_array.shape}; expected {self.EXPECTED_SHAPE}")
        if frame_array.dtype != np.float32:
            frame_array = frame_array.astype(np.float32)
        return frame_array

    def _normalize(self, frame_array: NDArray[np.float32]) -> NDArray[np.float32]:
        if frame_array.max(initial=0.0) > 1.0 or frame_array.min(initial=0.0) < 0.0:
            max_abs = float(np.abs(frame_array).max(initial=1.0))
            if max_abs > 0:
                return frame_array / max_abs
        return frame_array

    @staticmethod
    def _risk_for_detection(class_name: KnownClassName, distance_m: float) -> RiskLevel:
        if class_name in {"human", "animal"}:
            if distance_m < 10.0:
                return "critical"
            if distance_m < 25.0:
                return "warning"
        if class_name in {"rock", "post", "vehicle"} and distance_m < 5.0:
            return "critical"
        return "safe"

    @staticmethod
    def _collision_risk(detections: list[Detection]) -> str:
        if not detections:
            return "none"
        levels = {det.risk_level for det in detections}
        if "critical" in levels:
            return "high"
        if "warning" in levels:
            return "medium"
        return "low"

    def _decode_outputs(self, outputs: Any) -> list[Detection]:
        decoded: list[Detection] = []
        if isinstance(outputs, list):
            source = outputs
        elif isinstance(outputs, dict) and isinstance(outputs.get("detections"), list):
            source = outputs["detections"]
        else:
            return decoded

        for item in source:
            class_name = str(item.get("class_name", "vehicle"))
            if class_name not in KNOWN_CLASSES:
                continue
            typed_class_name = cast(KnownClassName, class_name)
            distance_m = float(item.get("distance_m", 999.0))
            risk = self._risk_for_detection(typed_class_name, distance_m)
            bbox = item.get("bbox_bev") or item.get("box") or [0.0, 0.0, 1.0, 1.0, 0.0]
            bbox = [float(v) for v in bbox[:5]] if len(bbox) >= 5 else [0.0, 0.0, 1.0, 1.0, 0.0]
            decoded.append(
                Detection(
                    class_name=typed_class_name,
                    confidence=float(item.get("confidence", item.get("score", 0.0))),
                    bbox_bev=bbox,
                    distance_m=distance_m,
                    risk_level=risk,
                )
            )
        return decoded

    def _decode_onnx_outputs(self, outputs: list[NDArray[np.float32]]) -> list[Detection]:
        if len(outputs) < 2:
            return []

        detections = outputs[0]
        confidence_scores = 1.0 / (1.0 + np.exp(-outputs[1]))
        if detections.ndim != 4 or confidence_scores.ndim != 4:
            return []

        conf_map = confidence_scores[0, 0]
        flat_indices = np.argsort(conf_map.reshape(-1))[::-1][:10]
        width = conf_map.shape[1]

        decoded: list[Detection] = []
        for flat_index in flat_indices:
            score = float(conf_map.reshape(-1)[flat_index])
            if score < 0.5:
                continue
            row = int(flat_index // width)
            col = int(flat_index % width)
            class_idx = int(np.argmax(detections[0, :, row, col]))
            class_name = KNOWN_CLASSES[class_idx] if class_idx < len(KNOWN_CLASSES) else "vehicle"
            typed_class_name = cast(KnownClassName, class_name)
            distance_m = max(1.0, float((detections.shape[-2] - row) * 0.25))
            decoded.append(
                Detection(
                    class_name=typed_class_name,
                    confidence=score,
                    bbox_bev=[float(col), float(row), 1.0, 1.0, 0.0],
                    distance_m=distance_m,
                    risk_level=self._risk_for_detection(typed_class_name, distance_m),
                )
            )
        return decoded

    def predict(self, frame_array: NDArray[np.float32]) -> list[Detection]:
        started = time.perf_counter()
        try:
            frame_array = self._normalize(self._validate_frame(frame_array))
            batched = np.expand_dims(frame_array, axis=0).astype(np.float32)

            if self.backend == "pytorch":
                if self.model is None:
                    raise RuntimeError("PyTorch model is not initialized")
                tensor = torch.from_numpy(frame_array).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    outputs = self.model(tensor)
                detections = self._decode_outputs(outputs)
            elif self.backend == "onnx":
                if self.onnx_session is None or self.onnx_input_name is None:
                    raise RuntimeError("ONNX session is not initialized")
                outputs = self.onnx_session.run(self.onnx_output_names, {self.onnx_input_name: batched})
                detections = self._decode_onnx_outputs(outputs)
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")

            self.last_collision_risk = self._collision_risk(detections)
            self._recent_success.append(True)
            return detections
        except Exception:
            self.failed_inferences += 1
            self._recent_success.append(False)
            raise
        finally:
            self._latencies_ms.append((time.perf_counter() - started) * 1000.0)
            self.total_inferences += 1

    def get_percentile_latency(self, p: int) -> float:
        if not self._latencies_ms:
            return 0.0
        return float(np.percentile(np.array(self._latencies_ms, dtype=np.float64), p))

    @property
    def avg_latency_ms(self) -> float:
        if not self._latencies_ms:
            return 0.0
        return float(np.mean(np.array(self._latencies_ms, dtype=np.float64)))

    def is_healthy(self) -> bool:
        if not self.model_loaded:
            return False
        if self.total_inferences >= self.min_healthy_inferences and len(self._recent_success) >= self.min_healthy_inferences:
            if not all(list(self._recent_success)[-self.min_healthy_inferences :]):
                return False
        return self.get_percentile_latency(95) < self.p95_latency_threshold_ms
