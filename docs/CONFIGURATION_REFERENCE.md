# Configuration Reference

## 1. Core Config Files
- `configs/base.yaml`: base model/data/eval settings.
- `configs/train.yaml`: training run parameters.
- `configs/retrain.yaml`: offline retraining configuration.
- `configs/mlflow.yaml`: tracking URI, experiment tags.
- `configs/server.yaml`: inference server host/model/limits/health.
- `configs/mining.yaml`: hard-case mining thresholds and behavior.
- `configs/safety_policy.yaml`: safety gate policy limits.
- `configs/platforms/*.yaml`: platform deployment profiles.

## 2. Environment Variables (`.env.example`)
- `MODEL_REGISTRY_PATH`
- `CHECKPOINT_DIR`
- `DATA_DIR`
- `LOG_LEVEL`
- `DRY_RUN`

## 3. Safety-Critical Fields
- `dangerous_fnr_hard_limit` (critical)
- `human_recall_minimum` (critical)
- `regression_tolerance` (critical)

## 4. Artifact Paths
- Checkpoints: `outputs/checkpoints/`
- Candidate runs: `outputs/candidates/`
- Reports: `outputs/reports/`
- Registry: `outputs/registry/registry.json`
- ONNX: `outputs/onnx/model.onnx`

## 5. Common Buyer/Integrator Tuning Knobs
- `data.batch_size`
- `device` / `model.device`
- `metrics.dangerous_classes`
- `metrics.latency_threshold_ms`
- `server.limits.rate_limit_per_second`
- `server.health.p95_latency_threshold_ms`

## 6. Sample Configuration Profiles

### Development
- CPU device, low batch size, verbose logging.

### Field Pilot
- Edge GPU backend, stricter thermal and health monitoring thresholds.

### Safe Dry-run
- `DRY_RUN=true` in environment.
- Run `make safety-check` and `make compare` before any promotion attempt.
