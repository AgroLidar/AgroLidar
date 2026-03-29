from __future__ import annotations

import base64
from collections import deque
from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

from inference_server.models import Detection


class FakePredictor:
    EXPECTED_SHAPE = (4, 512, 512)

    def __init__(self, *args, **kwargs):
        self.model_loaded = True
        self.model_version = "test-v1"
        self.checkpoint_path = "outputs/checkpoints/best.pt"
        self.device = "cpu"
        self.model_loaded_at = datetime.now(timezone.utc).timestamp()
        self.total_inferences = 0
        self.failed_inferences = 0
        self._latencies_ms = deque(maxlen=1000)
        self.last_collision_risk = "none"

    @property
    def avg_latency_ms(self) -> float:
        if not self._latencies_ms:
            return 0.0
        return float(sum(self._latencies_ms) / len(self._latencies_ms))

    def get_percentile_latency(self, p: int) -> float:
        if not self._latencies_ms:
            return 0.0
        return float(np.percentile(np.array(self._latencies_ms, dtype=np.float64), p))

    def is_healthy(self) -> bool:
        return self.model_loaded

    @property
    def last_latency_ms(self) -> float:
        return self._latencies_ms[-1] if self._latencies_ms else 0.0

    @property
    def supported_classes(self) -> list[str]:
        return ["human", "animal", "rock", "post", "vehicle"]

    @property
    def input_shape(self) -> tuple[int, int, int]:
        return self.EXPECTED_SHAPE

    def predict(self, frame_array: np.ndarray) -> list[Detection]:
        if frame_array.shape != self.EXPECTED_SHAPE:
            raise ValueError("Invalid shape")
        self.total_inferences += 1
        self._latencies_ms.append(10.0)

        if frame_array[0, 0, 0] > 0.5:
            self.last_collision_risk = "high"
            return [
                Detection(
                    class_name="human",
                    confidence=0.95,
                    bbox_bev=[100.0, 100.0, 20.0, 20.0, 0.0],
                    distance_m=4.0,
                    risk_level="critical",
                )
            ]

        self.last_collision_risk = "low"
        return [
            Detection(
                class_name="vehicle",
                confidence=0.82,
                bbox_bev=[200.0, 150.0, 15.0, 10.0, 0.1],
                distance_m=32.0,
                risk_level="safe",
            )
        ]


@pytest.fixture
def client(monkeypatch):
    import inference_server.main as main

    monkeypatch.setattr(main, "BEVPredictor", FakePredictor)
    with TestClient(main.app) as test_client:
        yield test_client


def _frame_b64(fill: float = 0.0) -> str:
    frame = np.full((4, 512, 512), fill, dtype=np.float32)
    return base64.b64encode(frame.tobytes()).decode("utf-8")


def _payload(frame_id: str = "frame-1", fill: float = 0.0) -> dict:
    return {
        "frame_data": _frame_b64(fill),
        "frame_id": frame_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
    }


def test_health_returns_200_when_model_loaded(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "degraded"}


def test_health_returns_503_when_model_not_loaded(client: TestClient):
    client.app.state.predictor.model_loaded = False
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["model_loaded"] is False


def test_predict_valid_frame_returns_detections(client: TestClient):
    response = client.post("/predict", json=_payload())
    assert response.status_code == 200
    assert len(response.json()["detections"]) >= 1


def test_predict_wrong_shape_returns_422(client: TestClient):
    bad = base64.b64encode(np.zeros((4, 128, 128), dtype=np.float32).tobytes()).decode("utf-8")
    payload = _payload()
    payload["frame_data"] = bad
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_invalid_base64_returns_422(client: TestClient):
    payload = _payload()
    payload["frame_data"] = "not-valid-base64"
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_response_has_required_fields(client: TestClient):
    response = client.post("/predict", json=_payload())
    body = response.json()
    required = {
        "frame_id",
        "timestamp",
        "detections",
        "inference_time_ms",
        "model_version",
        "dangerous_objects",
        "collision_risk",
    }
    assert required.issubset(body.keys())


def test_batch_predict_up_to_16_frames(client: TestClient):
    payload = [_payload(frame_id=f"frame-{idx}") for idx in range(16)]
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 16


def test_batch_predict_over_limit_returns_422(client: TestClient):
    payload = [_payload(frame_id=f"frame-{idx}") for idx in range(17)]
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 422


def test_metrics_endpoint_increments_after_predict(client: TestClient):
    before = client.get("/metrics").json()["successful_requests"]
    response = client.post("/predict", json=_payload())
    assert response.status_code == 200
    after = client.get("/metrics").json()["successful_requests"]
    assert after == before + 1


def test_collision_risk_high_when_human_detected_close(client: TestClient):
    response = client.post("/predict", json=_payload(fill=1.0))
    assert response.status_code == 200
    body = response.json()
    assert body["collision_risk"] == "high"
    assert body["dangerous_objects"] == 1


def test_ready_probe_returns_200(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200


def test_live_probe_returns_200(client: TestClient):
    response = client.get("/live")
    assert response.status_code == 200


def test_single_and_batch_prediction_are_consistent(client: TestClient):
    single = client.post("/predict", json=_payload(frame_id="frame-single")).json()
    batched = client.post("/predict/batch", json=[_payload(frame_id="frame-batch")]).json()[0]
    assert single["detections"][0]["class_name"] == batched["detections"][0]["class_name"]
    assert single["collision_risk"] == batched["collision_risk"]
