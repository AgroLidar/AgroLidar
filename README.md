[![CI](https://github.com/AgroLidar/AgroLidar/actions/workflows/ci.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/ci.yml)
[![Docs](https://github.com/AgroLidar/AgroLidar/actions/workflows/docs.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/docs.yml)
[![Repository Hygiene](https://github.com/AgroLidar/AgroLidar/actions/workflows/repo-hygiene.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/repo-hygiene.yml)
[![Release](https://github.com/AgroLidar/AgroLidar/actions/workflows/release.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

<p align="center">
  <img src="assets/logo.png" alt="AgroLidar" width="180" />
</p>

# AgroLidar

**AgroLidar is a production-minded LiDAR perception platform for agricultural machines**, designed for safety-oriented obstacle detection, model governance, and controlled continuous improvement from real-world field data.

It combines training, evaluation, model registry, safety gating, ONNX export, and API inference into a coherent operator-ready stack.

## Why AgroLidar

- **Field-first safety posture**: designed around hard classes like humans, animals, rocks, and posts.
- **Governed model promotion**: explicit candidate-vs-production comparisons before rollout.
- **Operationally practical**: includes server APIs, deployment docs, and platform adaptation configs.
- **Continuous learning loop**: mine hard cases, review, retrain, evaluate, and promote with policy checks.

## Core Features

- LiDAR data simulation, preprocessing, training, and inference.
- Safety-oriented metrics and promotion gates.
- FastAPI inference server (`inference_server/` and `lidar_perception/api/`).
- ONNX export + validation for runtime portability.
- Registry lifecycle (`production`, `candidate`, `archived`, `rejected`) managed by scripts.
- Config-driven platform profiles for agricultural vehicles.

## System Overview

```text
Data -> Train/Retrain -> Evaluate -> Compare -> Safety Gate -> Promote
  |                                                |
  +-> Hard-case mining + review queue              +-> Registry + reports
```

### Architecture Components

- `lidar_perception/`: model, data, inference, risk, evaluation, and registry logic.
- `scripts/`: CLI automation for train/eval/retrain/promotion/export.
- `inference_server/`: serving layer for online inference.
- `configs/`: base, training, evaluation, inference, safety, and platform profiles.
- `docs/`: deployment, operations, regulatory, and integration guides.

## Repository Structure

```text
AgroLidar/
├── lidar_perception/      # Core Python package
├── inference_server/      # FastAPI inference service
├── scripts/               # Training/evaluation/promotion automation
├── configs/               # Runtime + pipeline configuration
├── tests/                 # Unit and integration tests
├── docs/                  # Product and technical documentation
├── app/, components/      # Next.js landing page
└── outputs/               # Generated reports and registry state
```

## Quickstart

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Validate environment

```bash
python scripts/check_installation.py
```

### 3) Run an end-to-end smoke flow

```bash
make generate-data
make train
make evaluate
make safety-check
```

### 4) Serve inference API

```bash
make serve
# API: http://localhost:8000
```

## Usage Examples

### Train a baseline model

```bash
python scripts/train.py --config configs/train.yaml
```

### Retrain with hard-case emphasis

```bash
python scripts/retrain.py --config configs/retrain.yaml
```

### Compare candidate vs production

```bash
python scripts/compare_models.py \
  --production-metrics outputs/reports/production_eval.json \
  --candidate-metrics outputs/reports/eval_report.json
```

### Attempt controlled promotion

```bash
python scripts/promote_model.py \
  --candidate-model outputs/candidates/<run>/checkpoints/best.pt \
  --production-model outputs/checkpoints/best.pt \
  --comparison-report outputs/reports/model_comparison.json
```

## Development

```bash
make setup
make lint
make test
pre-commit run --all-files
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, branch strategy, and PR quality expectations.

## Documentation

- [Documentation Home](docs/index.md)
- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Usage Guide](docs/usage.md)
- [Development Guide](docs/development.md)
- [Roadmap](docs/roadmap.md)
- [Operations Manual](docs/OPERATIONS_MANUAL.md)
- [Safety and Limitations](docs/SAFETY_AND_LIMITATIONS.md)

## Demo / Screenshots

- Product demo placeholder: `docs/assets/demo.gif` (to be added once a stabilized demo capture is available).
- API example payloads and workflows are documented in [docs/API_INTEGRATION_GUIDE.md](docs/API_INTEGRATION_GUIDE.md).

## Project Status

AgroLidar is in active development toward an enterprise-ready v1.0 release.

- Current baseline line: `0.9.x`
- Planned release discipline: Semantic Versioning + changelog-driven releases
- See [CHANGELOG.md](CHANGELOG.md) and [docs/roadmap.md](docs/roadmap.md)

## Security

Please review [SECURITY.md](SECURITY.md) for vulnerability reporting and disclosure policy.

## Contributing

Community and team contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## Organization Contact

- GitHub: https://github.com/AgroLidar
- Security: security@agro-lidar.com
- General contact: contact@agro-lidar.com
