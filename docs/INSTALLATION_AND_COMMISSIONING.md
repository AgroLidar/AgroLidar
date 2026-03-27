# Installation and Commissioning

## 1. Pre-installation Checklist
- Confirm power budget and voltage (12V/24V) on target vehicle.
- Confirm mount location has clear forward FOV and protected cable route.
- Confirm repository setup and dependencies with `make setup` (from `docs/CONTRIBUTING.md`).
- Confirm required configs are present under `configs/`.

## 2. Mechanical Mounting Procedure
1. Install rigid bracket and vibration isolation as needed.
2. Mount LiDAR at planned height and pitch from platform profile (`configs/platforms/*.yaml`).
3. Torque fasteners to bracket vendor spec; mark with torque paint for inspection.
4. Route cables with strain relief; avoid moving pinch points.

## 3. Electrical Integration Overview
- Provide fused and regulated supply to compute and sensor subsystems.
- Validate cold-start and transient behavior.
- Confirm grounding strategy and shield termination.

## 4. Network Setup
- Local edge host: static IP recommended for commissioning.
- Expose inference API at configured host/port from `configs/server.yaml`.
- For remote support, add VPN or secure tunnel (production should avoid open ports).

## 5. Software Installation

### Option A: Local Python
```bash
make install
make setup
```

### Option B: Server container
```bash
make serve-docker
```
(Uses `Dockerfile.server`.)

### Option C: Full Docker build context
Use `Dockerfile` for pipeline-centric local environments.

## 6. Config Preparation
- Base runtime/config: `configs/base.yaml`
- Server runtime: `configs/server.yaml`
- Safety policy: `configs/safety_policy.yaml`
- MLflow: `configs/mlflow.yaml`
- Platform profile: `configs/platforms/<profile>.yaml`

## 7. First Boot Sequence
```bash
make registry-status
make serve
```
Then verify:
```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/model/info
```

## 8. First Sensor Data Validation
- Validate BEV frame shape and dtype against `docs/DATA_SCHEMA.md`.
- Confirm frame payload is base64 of float32 tensor with shape `(4, 512, 512)`.

## 9. First Inference Validation
```bash
make evaluate
make registry-status
```
If serving:
- `GET /health` should return healthy/degraded/unhealthy payload.
- `POST /predict` should return `PredictionResponse` with detections and `collision_risk`.

## 10. Commissioning Acceptance Checklist
- [ ] Sensor physically secure and calibrated.
- [ ] Power stable under startup and load changes.
- [ ] API health and readiness endpoints reachable.
- [ ] Checkpoint and registry files present.
- [ ] Baseline evaluation generated in `outputs/reports/`.
- [ ] Safety gate behavior reviewed on latest candidate report.

## 11. Useful Commands
```bash
make install
make setup
make serve
make evaluate
make safety-check
make registry-status
make export-onnx
make validate-onnx
make check-install
```

## 12. Troubleshooting

### No LiDAR frames received
- Verify sensor power and Ethernet wiring.
- Confirm ingest process provides BEV payloads (repo currently expects BEV-formatted input).

### Wrong BEV frame format
- Check shape `(4, 512, 512)`, float32, normalized values, and schema rules in `docs/DATA_SCHEMA.md`.

### Empty detections
- Check model load state via `/health` and `/model/info`.
- Confirm checkpoint exists at `outputs/checkpoints/best.pt`.

### Latency too high
- Check thermal throttling and compute utilization.
- Confirm `configs/server.yaml` backend/device settings.

### MLflow tracking not writing
- Verify `configs/mlflow.yaml` `tracking_uri` path is writable.

### Safety gate blocking
- Inspect `outputs/reports/gate_report.json` for `dangerous_fnr` and recall rule failures.

### ONNX inference mismatch
- Re-run `make validate-onnx` and inspect validation metadata in `outputs/onnx/export_metadata.json`.

### `registry.json` missing or corrupt
- Restore `outputs/registry/registry.json` from backup, or re-run promotion workflow after evaluation.
