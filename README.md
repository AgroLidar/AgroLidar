[![CI](https://github.com/AgroLidar/AgroLidar/actions/workflows/ci.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2-orange.svg)](https://pytorch.org/)
[![ONNX](https://img.shields.io/badge/ONNX-1.16-purple.svg)](https://onnx.ai/)
[![MLflow](https://img.shields.io/badge/MLflow-2.14-blue.svg)](https://mlflow.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Docs](https://img.shields.io/badge/docs-deployment%20ready-brightgreen.svg)](docs/README.md)
[![Safety Gate](https://img.shields.io/badge/safety%20gate-enabled-critical.svg)](docs/SAFETY_AND_LIMITATIONS.md)

# AgroLidar

AgroLidar is a **field-first LiDAR perception stack for agricultural machines**.

The system is built for safety-critical operation around people, animals, rocks, and posts in noisy real-world conditions (dust, vegetation clutter, uneven terrain).

> Policy: **no online self-training in production**. Models learn offline through review, retraining, and controlled promotion.

---

## Continuous Learning Loop

1. Run inference on collected runs.
2. Mine hard/failure cases into `data/hard_cases/`.
3. Build and review labeling queue in `data/review_queue/`.
4. Retrain a **candidate model** with base + reviewed hard cases.
5. Evaluate candidate on safety-critical metrics.
6. Compare candidate vs production and promote only if policy passes.

---

## Retraining with Hard Cases

`scripts/retrain.py` now composes datasets using:

- base training dataset
- reviewed hard-case dataset (`data/hard_cases/` + `data/review_queue/`)

Key knobs (in `configs/retrain.yaml`):

- `hard_case_ratio`
- `oversample_dangerous_classes`
- `dangerous_class_weight`
- `reviewed_only`
- `only_high_conf_failures`

Retraining writes metadata to `outputs/reports/retrain_metadata.json` and saves a **new candidate run** under `outputs/candidates/<tag_timestamp>/` (production artifacts are not overwritten).

---

## Safety-Critical Metrics

`scripts/evaluate.py` outputs both JSON and Markdown reports with:

- global: mAP, recall, precision, dangerous FNR, latency, robustness gap
- per-class safety metrics for:
  - `human`
  - `animal`
  - `rock`
  - `post`
  - `vehicle`
- per class:
  - recall
  - false negative rate
  - precision
  - distance error
- aggregate:
  - `dangerous_class_aggregate_score`

---

## Model Promotion Logic

`python scripts/promote_model.py ...` consumes:

- candidate model checkpoint
- production model checkpoint
- comparison report (`scripts/compare_models.py` output)

Promotion policy requires:

- improved safety recall / dangerous FNR
- no significant latency regression
- no significant robustness degradation

Outcomes:

- accepted candidate -> `production`
- previous production -> `archived`
- rejected candidate -> `rejected`

All state transitions are written in `outputs/registry/registry.json`.

---

## Quick Commands

```bash
python scripts/train.py --config configs/train.yaml
python scripts/retrain.py --config configs/retrain.yaml
python scripts/evaluate.py --config configs/base.yaml
python scripts/compare_models.py --production-metrics outputs/reports/production_eval.json --candidate-metrics outputs/reports/eval_report.json
python scripts/promote_model.py --candidate-model outputs/candidates/<run>/checkpoints/best.pt --production-model outputs/checkpoints/best.pt --comparison-report outputs/reports/model_comparison.json
```


## 📦 Deployment & Integration

### Quick Start (Sandbox)

```bash
make generate-data && make train && make serve
# Then POST a frame to http://localhost:8000/predict
```

### Verify Your Installation

```bash
make check-install
```

### Documentation

- [Deployment Documentation Index](docs/README.md)

### Hardware & Platform Compatibility

- [Hardware Deployment Guide](docs/HARDWARE_DEPLOYMENT_GUIDE.md)
- [Vehicle Compatibility Guide](docs/VEHICLE_COMPATIBILITY_GUIDE.md)
- [Platform Adaptation Matrix](docs/PLATFORM_ADAPTATION_MATRIX.md)

### For Buyers & Integrators

- [Buyer Checklist](docs/BUYER_CHECKLIST.md)
- [Sandbox and Demo Mode](docs/SANDBOX_AND_DEMO_MODE.md)
- [API Integration Guide](docs/API_INTEGRATION_GUIDE.md)

### Safety & Regulatory

- [Safety and Limitations](docs/SAFETY_AND_LIMITATIONS.md)
- [Regulatory and Compliance](docs/REGULATORY_AND_COMPLIANCE.md)
