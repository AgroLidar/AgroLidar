[![Continuous Integration](https://github.com/AgroLidar/AgroLidar/actions/workflows/ci.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/ci.yml)
[![Docs Validation](https://github.com/AgroLidar/AgroLidar/actions/workflows/docs.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/docs.yml)
[![GitHub Pages](https://github.com/AgroLidar/AgroLidar/actions/workflows/docs-pages.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/docs-pages.yml)
[![Release](https://github.com/AgroLidar/AgroLidar/actions/workflows/release.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/release.yml)
[![Security](https://github.com/AgroLidar/AgroLidar/actions/workflows/security.yml/badge.svg)](https://github.com/AgroLidar/AgroLidar/actions/workflows/security.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.9.0-informational.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

<p align="center">
  <img src="assets/logo.png" alt="AgroLidar" width="180" />
</p>

# AgroLidar

AgroLidar is a production-minded LiDAR perception platform for agricultural machines that unifies data generation, training, evaluation, safety gating, model promotion, and API serving so teams can ship safer field-ready models faster with traceable governance.

## Quickstart / First Run

### 1) Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Install frontend dependencies

```bash
npm ci
```

### 3) Verify installation

```bash
make check-install
# equivalent: python scripts/check_installation.py
```

### 4) Run backend / inference server

```bash
make serve
# equivalent: uvicorn inference_server.main:app --host 0.0.0.0 --port 8000
```

### 5) Run frontend

```bash
npm run dev
# app URL: http://localhost:3000
```

### 6) Run tests and quality checks

```bash
make test                # Python test suite
npm run lint             # Next.js lint checks
npm run typecheck        # TypeScript type checks
```

### 7) Optional smoke/demo flow

```bash
make generate-data
make train
make evaluate
make safety-check
```


## Web Simulator

AgroLidar now uses the simulator as the default web entrypoint: `/` redirects to `/simulator` in production (including Vercel), while the previous marketing landing page moved to `/legacy`.

### Multi-vehicle flagship simulator

The simulator now ships two selectable mission platforms in one shared world/state:

- **Tractor**: ground hazard operations with close-range obstacle awareness
- **Agro Drone**: heavy-lift aerial platform inspired by AGRAS-class agricultural aircraft

Switch vehicles via the top segmented selector or `V`. Seed/scenario/weather continuity is preserved during vehicle swaps.

### Drone mission modes

Press `1`–`4` (or use the control panel) to switch drone mission profile:

1. `Spray` (swath-oriented crop treatment)
2. `Spread` (granular distribution behavior)
3. `Lift` (heavier handling + sling payload)
4. `LiDAR Survey` (mapping/coverage hero mode)

### Controls

- `W` / `ArrowUp`: forward
- `S` / `ArrowDown`: backward
- `A` / `ArrowLeft`: steer (tractor) / strafe (drone) left
- `D` / `ArrowRight`: steer (tractor) / strafe (drone) right
- `Space`: drone ascend
- `Shift`: drone descend
- `Q` / `E`: drone yaw left/right
- `R`: reset active vehicle
- `C`: cycle vehicle-specific cameras
- `P`: pause/resume
- `H`: show/hide HUD
- `L`: cycle LiDAR rendering modes
- `M`: toggle minimap/mission map
- `V`: switch vehicle

### 4K / presentation mode

- Toggle `4K` in the quick controls for premium demos.
- Uses DPR clamping + adjustable render scale for browser-stable high-resolution output.
- Quality presets now include `Ultra / Presentation` with graceful fallback (no forced full native 4K render load).

### Browser compatibility

- Browser-native WebGL path (Vercel friendly)
- Tuned for modern **Chrome**, **Safari**, **Opera**, and Chromium/WebKit browsers
- Dynamic rendering controls to keep frame pacing stable across desktop/mobile hardware

### Run locally

```bash
npm ci
npm run dev
# open http://localhost:3000 (auto-redirects to /simulator)
```

### Production build

```bash
npm run build
npm run start
```

### Vercel deployment model

The simulator core loop runs entirely on the client (React + Three.js in the browser), so it deploys to Vercel without any custom realtime backend service requirements.

## Architecture at a glance

- `lidar_perception/`: model, data, training, evaluation, and registry-facing core logic.
- `inference_server/`: FastAPI app, prediction interfaces, middleware, and health checks.
- `scripts/`: CLI workflows (train/evaluate/retrain/promote/export/check-install).
- `configs/`: YAML configuration for training, inference, retraining, and safety policy.
- `app/` + `components/`: Next.js public-facing UI and reusable UI primitives.
- `docs/`: operations, architecture, integration, safety, and deployment documentation.
- `tests/`: backend regression and contract test coverage.

## Trust, governance, and community

- Contributing guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Support policy: [SUPPORT.md](SUPPORT.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- License: [LICENSE](LICENSE)
- Code ownership: [.github/CODEOWNERS](.github/CODEOWNERS)

## Why AgroLidar

- **Field-first safety posture** for hard classes like humans, animals, rocks, and posts.
- **Governed model promotion** with explicit candidate-vs-production comparisons before rollout.
- **Operationally practical** delivery: APIs, deployment docs, and platform adaptation configs.
- **Continuous learning loop** to mine hard cases, review, retrain, evaluate, and promote with policy checks.

## Core Features

- LiDAR data simulation, preprocessing, training, and inference.
- Safety-oriented metrics and promotion gates.
- FastAPI inference server (`inference_server/`) with runtime model loading and health endpoints.
- ONNX export + validation for runtime portability.
- Registry lifecycle (`production`, `candidate`, `archived`, `rejected`) managed by scripts.
- Config-driven platform profiles for agricultural vehicles.

## System Overview

```text
Data -> Train/Retrain -> Evaluate -> Compare -> Safety Gate -> Promote
  |                                                |
  +-> Hard-case mining + review queue              +-> Registry + reports
```

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

## Release & Versioning

- AgroLidar follows **Semantic Versioning**.
- Canonical release metadata is kept in `VERSION`, `lidar_perception.__version__`, and `package.json`.
- Changelog-first release discipline: see [CHANGELOG.md](CHANGELOG.md).
- Release process: [docs/release-process.md](docs/release-process.md).
- Pre-flight release checks: [docs/release-checklist.md](docs/release-checklist.md).

## Documentation

- **Docs home**: [docs/index.md](docs/index.md)
- **MkDocs config**: [mkdocs.yml](mkdocs.yml)
- **Getting Started**: [docs/getting-started.md](docs/getting-started.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Operations Manual**: [docs/OPERATIONS_MANUAL.md](docs/OPERATIONS_MANUAL.md)
- **Safety & Limitations**: [docs/SAFETY_AND_LIMITATIONS.md](docs/SAFETY_AND_LIMITATIONS.md)
- **Roadmap**: [docs/roadmap.md](docs/roadmap.md)

> After GitHub Pages is enabled, docs are published from the Pages workflow.

## Development

```bash
make setup
make lint
make test
pre-commit run --all-files
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch strategy, testing, and PR quality expectations.

## Project Status

AgroLidar is in active development toward an enterprise-ready `v1.0.0` release.

- Current baseline line: `0.9.x`
- Planned release discipline: Semantic Versioning + changelog-driven releases
- See [CHANGELOG.md](CHANGELOG.md) and [docs/roadmap.md](docs/roadmap.md)

## Security

Please review [SECURITY.md](SECURITY.md) for vulnerability reporting and disclosure expectations.
Dependency audit behavior (including `requirements.audit.txt` and narrow temporary advisory ignores) is documented in [SECURITY_NOTES.md](SECURITY_NOTES.md).
