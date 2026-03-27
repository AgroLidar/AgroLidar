# API Integration Guide

## 1. Overview
`inference_server` exposes REST endpoints for onboard systems, HMIs, telematics systems, and cloud services.

Base URL default: `http://<host>:8000`

## 2. Endpoints and Schemas
- `GET /health` → `HealthResponse`
- `GET /metrics` → `MetricsResponse`
- `GET /model/info` → model metadata payload
- `GET /ready` → Kubernetes readiness probe
- `GET /live` → Kubernetes liveness probe
- `POST /predict` → `BEVFrameInput` to `PredictionResponse`
- `POST /predict/batch` → `list[BEVFrameInput]` to `list[PredictionResponse]`

See `inference_server/models.py` for field-level schema constraints.

## 3. BEV Frame Encoding for `/predict`
- Prepare float32 tensor shape `(4, 512, 512)`.
- Serialize bytes and base64 encode.
- Send JSON payload with `frame_data`, `frame_id`, `timestamp`, optional `metadata`.

Frame contract reference: `docs/DATA_SCHEMA.md`.

## 4. Risk Mapping Guidance
Suggested external mapping:
- `high` → emergency stop signal path
- `medium` → slow-down + operator alert
- `low` / `none` → normal operation with continued monitoring

Final actuation policy is integrator-owned and must be validated per platform.

## 5. Integration Patterns
- Polling REST client on onboard compute.
- Embedded Linux Python client (example below).
- ROS 2 adapter pattern (future architecture).
- CAN bridge pattern (future architecture).

## 6. Rate Limits and Throughput
- Default limit: **100 req/s** from `configs/server.yaml`.
- Batch requests bounded by `max_batch_size`.

## 7. Health Monitoring
- Poll `/health` plus `/ready` for model readiness.
- Treat HTTP 503 as degraded perception state.

## 8. Authentication Status
Current API has no built-in authentication. For production integration, use network segmentation and add mTLS/API key gateway controls.

## 9. Versioning and Audit
Use `model_version` in `PredictionResponse` for traceability in logs and incident analysis.

## 10. Minimal Python Client Example
```python
import base64
from datetime import datetime, timezone

import numpy as np
import requests

frame = np.zeros((4, 512, 512), dtype=np.float32)
payload = {
    "frame_data": base64.b64encode(frame.tobytes()).decode("utf-8"),
    "frame_id": "demo_0001",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "metadata": {"source": "integration_test"},
}

resp = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=2.0)
resp.raise_for_status()
print(resp.json())
```
