# AgroLidar

AgroLidar is a **field-first agricultural LiDAR perception platform** for tractors and agricultural machines.

It is designed for safety-critical operation in unstructured environments with:
- uneven terrain
- sparse returns
- vegetation clutter
- dust/rain/low visibility
- moving people/animals near heavy machinery

> Product philosophy: **no unsafe online self-training in production.**
> Inference collects uncertainty and failures; learning is handled offline through controlled retraining and promotion.

---

## What this repository now includes

- Config-driven **training / validation / testing / inference** pipelines
- Dedicated **risk and hazard scoring** module (class priority + geometry + confidence + speed)
- Temporal-aware inference with tracking and stop-zone context
- **Hard-case mining** and failure manifest generation
- **Active-learning review queue** builder with reason codes
- **Offline retraining** entrypoint with hard-case metadata logging
- **Model comparison + promotion policy** logic
- Lightweight **model registry/versioning** under `outputs/registry/`
- Machine-readable and human-readable evaluation reports
- Tests for core pipeline interfaces

---

## Repository structure

```text
AgroLidar/
├── assets/
├── configs/
│   ├── base.yaml
│   ├── train.yaml
│   ├── eval.yaml
│   ├── infer.yaml
│   ├── active_learning.yaml
│   └── retrain.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── labels/
│   ├── hard_cases/
│   ├── review_queue/
│   └── manifests/
├── lidar_perception/
│   ├── active_learning/
│   ├── data/
│   ├── evaluation/
│   ├── inference/
│   ├── models/
│   ├── registry/
│   ├── risk/
│   ├── simulation/
│   ├── training/
│   └── utils/
├── scripts/
├── outputs/
│   ├── checkpoints/
│   ├── metrics/
│   ├── predictions/
│   ├── reports/
│   └── registry/
└── tests/
```

---

## End-to-end continuous improvement workflow

1. **Run inference** on new field logs.
2. **Mine failures / hard cases** (low confidence, near-miss risk, unstable tracks, dangerous misses).
3. Save structured hard-case artifacts under `data/hard_cases/`.
4. Build **review queue** for human labeling/verification in `data/review_queue/`.
5. **Retrain offline** with base data + reviewed hard cases.
6. **Evaluate candidate model** and compare against production.
7. Promote candidate only if safety-critical metrics improve and latency regression is controlled.

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## CLI quickstart

### Train
```bash
python scripts/train.py --config configs/train.yaml
```

### Evaluate
```bash
python scripts/evaluate.py --config configs/eval.yaml --checkpoint outputs/checkpoints/best.pt
```

### Infer (single or sequence)
```bash
python scripts/infer.py --config configs/infer.yaml --checkpoint outputs/checkpoints/best.pt --sample-index 0 --sequence-length 3 --save-json
```

### Mine hard cases
```bash
python scripts/mine_hard_cases.py --config configs/active_learning.yaml --checkpoint outputs/checkpoints/best.pt
```

### Build review queue
```bash
python scripts/build_review_queue.py --config configs/active_learning.yaml --hard-manifest data/hard_cases/manifest.jsonl
```

### Retrain offline
```bash
python scripts/retrain.py --config configs/retrain.yaml --resume outputs/checkpoints/latest.pt
```

### Compare production vs candidate
```bash
python scripts/compare_models.py --production-metrics outputs/reports/production_eval.json --candidate-metrics outputs/reports/eval_report.json
```

### Register model version
```bash
python scripts/register_model.py --config configs/train.yaml --checkpoint outputs/checkpoints/best.pt --metrics outputs/reports/eval_report.json --status candidate --version v0.2.0
```

---

## Core metrics tracked

- detection: mAP / precision / recall
- obstacle distance MAE
- segmentation IoU
- dangerous false-negative rate
- latency (ms) and FPS
- robustness gap under perturbations

Safety-critical promotion focuses on recall and dangerous-class misses (`human`, `animal`, `rock`, `post`) before deployment.

---

## Dataset abstraction (future real data ready)

Current adapters support:
- synthetic agricultural scenes
- folder-based `.bin` / `.pcd`
- manifest-based future tractor logs (`dataset_type: manifest`)

Manifest format is JSONL with `point_cloud`, optional `sample_id`, and metadata.

---

## Outputs and artifacts

- `outputs/checkpoints/`: latest and best model snapshots
- `outputs/metrics/`: epoch-level training metrics JSONL
- `outputs/predictions/`: inference JSON predictions
- `outputs/reports/`: evaluation and comparison reports
- `outputs/registry/registry.json`: model lifecycle entries

---

## Assumptions and roadmap

This foundation is production-oriented but currently synthetic-first for data availability.

Planned next steps:
- real tractor log adapters and labeling QA tools
- stronger temporal consistency scoring from sensor odometry
- edge deployment packaging (TorchScript/ONNX/TensorRT)
- richer condition-aware active-learning policies (weather/soil/crop stage)

