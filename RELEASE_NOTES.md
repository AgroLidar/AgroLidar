# AgroLidar v0.9.0 — Field-Ready Perception Stack

Release date: 2026-03-27

## What’s included

### Core Pipeline
- BEV LiDAR perception model (PyTorch, CPU/GPU)
- train → retrain → evaluate → safety gate → compare → promote
- Continuous learning loop with offline retraining policy

### Inference Server
- FastAPI server with /predict, /health, /metrics, /ready, /live
- Rate limiting (100 req/s), structured logging, CORS
- Docker deployment support (Dockerfile.server)

### ONNX Export
- Export PyTorch → ONNX with validation (max diff < 1e-4)
- ONNX Runtime inference backend option
- Benchmark: latency comparison PyTorch vs ONNX

### Safety
- Safety gate with configurable policy (configs/safety_policy.yaml)
- dangerous_fnr hard limit: 10% | human recall minimum: 90%
- Automatic PR comment with gate decision

### MLflow Tracking
- Full experiment tracking (params, metrics, artifacts)
- Local tracking server (make mlflow-ui)

### CI/CD
- GitHub Actions: lint, test, evaluate, smoke-train (all green)
- Pre-commit hooks: ruff, mypy, config validation
- PR quality gate with format check and secret scan

### Documentation
- 15 deployment docs covering hardware, installation, calibration, operations, safety, API, platforms, regulatory
- Platform compatibility guide: 200+ vehicle families
- PLATFORM_ADAPTATION_MATRIX covering 5 vehicle categories

### Platform Support
- configs/platforms/ with 9 reference profiles
- lidar_perception/platforms/platform_profiles.py

### Known Limitations
- Trained on synthetic data only — field validation required
- No real sensor ingest adapter (PCAP/ROS bag)
- No API authentication (development use only)
- Edge deployment on Jetson not yet validated
