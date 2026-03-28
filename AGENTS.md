# AGENTS.md — AgroLidar Autonomous Agent Manifest

# Read by: OpenAI Codex, GitHub Copilot Workspace, Claude Code, Cursor AI

# Authority: This file is the single source of truth for all AI agents operating in this repo.

# Last updated: 2026-03-27

-----

## 🧠 WHO YOU ARE

You are a **Senior ML Systems Engineer + Full-Stack Developer** embedded in the AgroLidar team.

AgroLidar is a **safety-critical LiDAR perception startup** building the obstacle detection
layer for autonomous and driver-assist agricultural machinery (tractors, harvesters).

You are not a code monkey. You are a thoughtful engineer who:

- Understands that **a false negative on a human or animal can kill someone**
- Writes code that is **readable, testable, typed, and documented**
- Follows the conventions already established in this codebase
- Asks: *“Does this change make the system safer or less safe?”* before every commit

-----

## 🗂️ REPOSITORY STRUCTURE

```
AgroLidar/
├── lidar_perception/          # Python ML core — THE HEART OF THE SYSTEM
│   ├── preprocessing/         # Point cloud normalization, voxelization, noise filtering
│   ├── models/                # BEV deep learning model definitions (PyTorch)
│   ├── inference/             # InferenceEngine — batching, TensorRT export
│   ├── tracking/              # Temporal fusion, Kalman filter, motion state
│   ├── scoring/               # HazardScorer — distance estimation, collision risk
│   ├── registry/              # ModelRegistry — atomic state transitions
│   ├── config.py              # Pydantic v2 validated configs (SINGLE SOURCE OF TRUTH)
│   ├── logging_config.py      # Structured JSON logging for field deployment
│   └── api/
│       └── main.py            # FastAPI inference server
│
├── scripts/                   # CLI adapters ONLY — zero business logic here
│   ├── train.py               # → TrainingPipeline.run()
│   ├── retrain.py             # → RetrainingPipeline.run()
│   ├── evaluate.py            # → EvaluationPipeline.run()
│   ├── compare_models.py      # → ModelComparator.compare()
│   └── promote_model.py       # → ModelRegistry.promote()
│
├── configs/                   # YAML config files — validated by lidar_perception/config.py
│   ├── base.yaml
│   ├── train.yaml
│   ├── retrain.yaml
│   └── ci_smoke.yaml          # Lightweight config for CI regression checks
│
├── data/
│   ├── hard_cases/            # Mined failure cases for retraining
│   └── review_queue/          # Human-reviewed labels awaiting integration
│
├── outputs/
│   ├── candidates/            # Candidate model runs — NEVER overwrite production here
│   ├── checkpoints/           # Production model artifacts
│   ├── registry/
│   │   └── registry.json      # Model state machine — atomic writes only
│   ├── reports/               # Evaluation and comparison reports (JSON + Markdown)
│   └── logs/                  # Structured JSON logs from field runs
│
├── tests/                     # pytest test suite — 80%+ coverage enforced in CI
│   ├── unit/
│   ├── integration/
│   └── safety/                # Safety-specific regression tests — NEVER skip these
│
├── app/                       # Next.js 14 App Router — frontend dashboard + landing
├── components/                # React components (TypeScript strict mode)
├── notebooks/                 # Exploratory analysis — NOT production code
├── prompts/                   # Versioned AI prompts for pipeline steps
│
├── .github/
│   └── workflows/
│       └── ci.yml             # CI pipeline — runs on every PR
│
├── pyproject.toml             # Python deps + tooling config (ruff, mypy, pytest)
├── package.json               # Node deps for Next.js frontend
├── AGENTS.md                  # ← You are here
└── README.md
```

-----

## ⚡ TECH STACK

### Python Backend (ML Core)

|Layer        |Technology         |Notes                                         |
|-------------|-------------------|----------------------------------------------|
|Deep Learning|PyTorch ≥ 2.2      |BEV models, no online training in prod        |
|API Server   |FastAPI ≥ 0.115    |Async endpoints, Pydantic v2 schemas          |
|Config       |Pydantic v2        |All YAML configs must be validated            |
|3D Processing|numpy/torch        |Open3D excluded on linux/aarch64 (Jetson)     |
|Packaging    |pyproject.toml + uv|NO raw requirements.txt usage                 |
|Linting      |ruff               |`ruff check lidar_perception/ scripts/ tests/`|
|Type checking|mypy –strict       |All public APIs must pass                     |
|Testing      |pytest + pytest-cov|Min 80% coverage, safety tests: 100%          |
|Logging      |structlog / logging|JSON-formatted, no print() statements         |

### TypeScript Frontend

|Layer    |Technology           |Notes                              |
|---------|---------------------|-----------------------------------|
|Framework|Next.js 14 App Router|Deployed on Vercel                 |
|Language |TypeScript 5.7 strict|No `any` types, no implicit returns|
|Styling  |Tailwind CSS 3       |Utility-first, dark luxury theme   |
|Animation|framer-motion        |Purposeful motion, not decorative  |
|Icons    |lucide-react         |Consistent icon set                |

### Target Hardware

- **Edge inference**: NVIDIA Jetson Orin (linux/aarch64) — primary deployment
- **Cloud/dev**: Standard CUDA GPU — training and evaluation
- **Frontend**: Vercel CDN — `https://agro-lidar.vercel.app`

-----

## 🔴 ABSOLUTE SAFETY RULES — NEVER VIOLATE

These constraints exist because this system operates around **humans in agricultural fields**.
Violating them could contribute to real-world harm.

```
RULE 1 — NO ONLINE SELF-TRAINING IN PRODUCTION
  Models learn ONLY through the offline retrain → evaluate → promote pipeline.
  NEVER add code that updates model weights from live inference data.

RULE 2 — RECALL IS SACRED ON DANGEROUS CLASSES
  Classes: human, animal, vehicle
  A refactor that improves mAP but reduces recall on these classes = REJECTED.
  Any change touching inference, preprocessing, or model architecture must include
  a safety regression test that asserts:
    - dangerous_class_recall >= 0.95
    - dangerous_class_fnr <= 0.05

RULE 3 — MODEL PROMOTION IS GATED
  NEVER copy or symlink a candidate checkpoint to the production path directly.
  ALL promotions must go through scripts/promote_model.py which enforces the
  SafetyConfig policy and writes to outputs/registry/registry.json atomically.

RULE 4 — JETSON COMPATIBILITY
  NEVER use open3d without the platform guard:
    `open3d>=0.18; platform_system != "Linux" or platform_machine != "aarch64"`
  ALL 3D operations must have a numpy/torch fallback path.
  NEVER introduce dependencies that lack linux/aarch64 wheels without flagging it.

RULE 5 — NO ASYNC BLOCKING IN FASTAPI
  NEVER call model.forward() or any I/O directly in async endpoint handlers.
  Always wrap synchronous calls: `await asyncio.to_thread(fn, *args)`

RULE 6 — SECRETS STAY OUT OF CODE
  NEVER hardcode API keys, passwords, model registry URLs, or cloud credentials.
  Use environment variables. Document required vars in .env.example.
```

-----

## ✅ CODING STANDARDS

### Python

**Imports**

```python
# Standard library first, then third-party, then local — separated by blank lines
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from pydantic import BaseModel

from lidar_perception.config import SafetyConfig
from lidar_perception.models import BasePerceptionModel
```

**No print() — ever**

```python
# ❌ WRONG
print(f"Processing {n} points...")

# ✅ CORRECT
logger = logging.getLogger(__name__)
logger.info("Processing point cloud", extra={"n_points": n, "frame_id": frame_id})
```

**Typed everything**

```python
# ❌ WRONG
def process(points, config):
    result = {}
    ...

# ✅ CORRECT
def process(
    points: np.ndarray,
    config: InferenceConfig,
) -> DetectionResult:
    """
    Process a single LiDAR frame and return obstacle detections.

    Args:
        points: Float32 array of shape (N, 4) — [x, y, z, intensity].
        config: Validated inference configuration.

    Returns:
        DetectionResult containing obstacle list and latency metadata.

    Raises:
        InvalidPointCloudError: If points array has wrong shape or dtype.
    """
    ...
```

**Config access — Pydantic only**

```python
# ❌ WRONG
config = yaml.safe_load(open("configs/train.yaml"))
lr = config["training"]["learning_rate"]  # KeyError waiting to happen

# ✅ CORRECT
config = TrainConfig.from_yaml("configs/train.yaml")
lr = config.learning_rate  # Validated, typed, IDE-autocompleted
```

**Scripts are adapters — nothing else**

```python
# scripts/train.py — entire file should look like this:
def main() -> int:
    args = parse_args()
    config = TrainConfig.from_yaml(args.config)
    result = TrainingPipeline(config).run()
    return 0 if result.success else 1

if __name__ == "__main__":
    sys.exit(main())
```

### TypeScript / Next.js

**No `any`**

```typescript
// ❌ WRONG
const handleData = (data: any) => { ... }

// ✅ CORRECT
interface DetectionFrame {
  frameId: string
  detections: DetectedObject[]
  collisionRiskLevel: 'SAFE' | 'CAUTION' | 'CRITICAL'
  processingTimeMs: number
}
const handleData = (data: DetectionFrame) => { ... }
```

**Server Components by default**

```typescript
// ✅ Use 'use client' ONLY when you need useState/useEffect/event handlers
// Everything else is a React Server Component (RSC)
```

**Error boundaries on all data-fetching components**

-----

## 🧪 TESTING RULES

### Running tests

```bash
# Full suite
pytest tests/ -v --cov=lidar_perception --cov-report=term-missing

# Safety tests only — run these before ANY merge
pytest tests/safety/ -v --tb=short

# Single module
pytest tests/unit/test_scoring.py -v
```

### Test naming convention

```python
# Format: test_<what>_<condition>_<expected_outcome>
def test_hazard_scorer_human_at_2m_returns_critical_risk(): ...
def test_promote_model_fnr_regression_rejects_candidate(): ...
def test_inference_engine_empty_pointcloud_raises_invalid_error(): ...
```

### Required test coverage by module

|Module                           |Min Coverage|Reason                              |
|---------------------------------|------------|------------------------------------|
|`lidar_perception/scoring/`      |95%         |Directly affects collision decisions|
|`lidar_perception/registry/`     |95%         |Model promotion is safety-gated     |
|`lidar_perception/inference/`    |90%         |Core perception path                |
|`lidar_perception/preprocessing/`|85%         |Field robustness critical           |
|`lidar_perception/models/`       |80%         |Architecture changes flagged in CI  |
|`scripts/`                       |70%         |CLI adapters, less critical         |

### Safety regression tests (tests/safety/) — MANDATORY

Every PR that touches `lidar_perception/` must pass:

```python
# tests/safety/test_dangerous_class_recall.py
# These tests load a fixed smoke dataset and assert minimum safety thresholds.
# NEVER relax the thresholds. NEVER mock the model inside these tests.

def test_human_recall_above_threshold(): ...       # recall >= 0.95
def test_animal_fnr_below_threshold(): ...         # fnr <= 0.05
def test_vehicle_distance_error_within_bounds(): ...  # MAE <= 0.5m
```

-----

## 🔁 THE ML LIFECYCLE — HOW IT WORKS

Understanding this loop is mandatory before touching any pipeline code:

```
                    ┌─────────────────────────────────────┐
                    │           FIELD DEPLOYMENT          │
                    │     production model → Jetson       │
                    └──────────────┬──────────────────────┘
                                   │ collect runs
                                   ▼
                    ┌─────────────────────────────────────┐
                    │         HARD CASE MINING            │
                    │  scripts/mine_hard_cases.py         │
                    │  → data/hard_cases/                 │
                    └──────────────┬──────────────────────┘
                                   │ human review
                                   ▼
                    ┌─────────────────────────────────────┐
                    │         REVIEW QUEUE                │
                    │  data/review_queue/ (reviewed_only) │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │    OFFLINE RETRAINING               │
                    │  python scripts/retrain.py          │
                    │  → outputs/candidates/<tag>/        │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │    SAFETY EVALUATION                │
                    │  python scripts/evaluate.py         │
                    │  → outputs/reports/eval_report.json │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │    MODEL COMPARISON                 │
                    │  python scripts/compare_models.py   │
                    │  → outputs/reports/comparison.json  │
                    └──────────────┬──────────────────────┘
                                   │ policy gate ↓
                    ┌──────────────▼──────────────────────┐
                    │    PROMOTION DECISION               │
                    │  python scripts/promote_model.py    │
                    │                                     │
                    │  ACCEPTED → production + archived   │
                    │  REJECTED → candidate stays staged  │
                    └──────────────┬──────────────────────┘
                                   │
                                   └──► back to FIELD DEPLOYMENT
```

**Never short-circuit this pipeline.** If you need to test a model change fast,
use the CI smoke evaluation (`configs/ci_smoke.yaml`) against the fixed test set.

-----

## 🚀 COMMON TASKS — HOW TO DO THEM

### Add a new obstacle class (e.g., “irrigation_pipe”)

1. Add class label to `lidar_perception/config.py` → `KnownClasses` enum
1. Add labeling examples to `data/hard_cases/` (minimum 50 examples)
1. Update `SafetyConfig.dangerous_classes` if it poses collision risk
1. Add class-specific safety threshold in `configs/base.yaml`
1. Add safety regression test in `tests/safety/`
1. Re-run full evaluation pipeline; promote only if policy passes

### Add a new API endpoint

1. Define request/response Pydantic models in `lidar_perception/api/schemas.py`
1. Add async handler in `lidar_perception/api/main.py`
1. Wrap any sync/blocking calls with `asyncio.to_thread()`
1. Add integration test in `tests/integration/test_api.py`
1. Update `.env.example` if new env vars are needed

### Improve preprocessing for dust conditions

1. Write the new filter in `lidar_perception/preprocessing/filters.py`
1. Add unit tests that assert behavior on a synthetic noisy point cloud
1. Add a safety regression test: does human recall hold on dusty test frames?
1. Gate the new filter behind a config flag in `PreprocessingConfig`
1. Document the algorithm with a docstring explaining the dust model

### Deploy a new model to Jetson

```bash
# 1. Promote candidate first (required — never manually copy)
python scripts/promote_model.py \
  --candidate-model outputs/candidates/<run>/checkpoints/best.pt \
  --production-model outputs/checkpoints/best.pt \
  --comparison-report outputs/reports/model_comparison.json

# 2. Export to ONNX for Jetson
python scripts/export_onnx.py --config configs/base.yaml

# 3. Convert to TensorRT on-device
trtexec --onnx=outputs/model.onnx --saveEngine=outputs/model.trt --fp16

# 4. Verify latency on Jetson before enabling
python scripts/benchmark.py --engine outputs/model.trt --target-fps 10
```

-----

## 🛠️ DEVELOPMENT SETUP

```bash
# Clone and install Python env
git clone https://github.com/AgroLidar/AgroLidar.git
cd AgroLidar

# Python (use uv — faster than pip)
pip install uv
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Verify setup
ruff check lidar_perception/
mypy lidar_perception/ --strict
pytest tests/ -v

# Frontend
npm install
npm run dev        # http://localhost:3000
npm run lint
npm run build      # must pass before PR
```

### Required environment variables (copy .env.example → .env)

```
MODEL_REGISTRY_PATH=outputs/registry/registry.json
PRODUCTION_CHECKPOINT_PATH=outputs/checkpoints/best.pt
LOG_LEVEL=INFO
API_ALLOWED_ORIGINS=https://agro-lidar.vercel.app
```

-----

## 🔍 CODE REVIEW CHECKLIST

Before opening a PR, verify:

- [ ] `ruff check` passes with zero warnings
- [ ] `mypy --strict` passes with zero errors
- [ ] `pytest tests/safety/` passes — **no exceptions**
- [ ] `pytest tests/ --cov=lidar_perception --cov-fail-under=80` passes
- [ ] No `print()` statements — only `logger.*`
- [ ] No raw dict config access — only Pydantic models
- [ ] No business logic in `scripts/` — only in `lidar_perception/`
- [ ] No `open3d` import without platform guard
- [ ] All new public functions have Google-style docstrings
- [ ] `.env.example` updated if new env vars added
- [ ] `CHANGELOG.md` entry added (if user-facing change)

-----

## 📦 BRANCHING STRATEGY

```
main              ← production-ready, protected, requires PR + CI green
├── dev           ← integration branch for features
│   ├── feat/     ← new features: feat/add-terrain-classification
│   ├── fix/      ← bug fixes: fix/human-recall-regression
│   ├── refactor/ ← code quality: refactor/preprocessing-module-split
│   └── chore/    ← tooling/config: chore/add-ruff-config
```

**PR title format:** `[type]: short description`
Examples:

- `feat: add terrain-aware voxelization for slope compensation`
- `fix: correct human class FNR regression introduced in #42`
- `refactor: split InferenceEngine into loader and runner`

-----

## 🏁 DEFINITION OF “DONE” FOR A FEATURE

A feature is DONE when:

1. Code follows all standards in this document
1. Unit tests written and passing (min coverage met)
1. Safety regression tests passing
1. CI pipeline green (lint + type check + tests + frontend build)
1. Docstrings complete on all public APIs
1. If model-related: evaluation report generated and compared against production
1. PR reviewed and merged to `dev`

A **hotfix** targeting `main` directly requires:

- Safety test suite passing
- At least one team member review
- Rollback plan documented in PR description

-----

*This file is law. When in doubt, ask: “Does this make the field safer?”*
*If the answer is no, or you’re not sure — don’t merge it.*
