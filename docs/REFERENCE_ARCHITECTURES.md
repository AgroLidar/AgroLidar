# Reference Architectures

## 1. End-to-End Data Flow

```mermaid
flowchart LR
  A[sensor] --> B[ingest]
  B --> C[BEV projection]
  C --> D[inference_server]
  D --> E[hazard logic]
  D --> F[logs]
  F --> G[mine_hard_cases]
  G --> H[review_queue]
  H --> I[retrain]
  I --> J[safety_gate]
  J --> K[compare]
  K --> L[promote]
  L --> M[production registry]
```

## 2. Deployment Modes
- Offline evaluation workstation: training/evaluation only.
- Edge inference on vehicle: `inference_server/` + checkpoint.
- Edge + cloud retraining: edge logs + offline review/retrain/gate/promotion.

## 3. Repository Component Mapping
- `scripts/`: train/retrain/evaluate/gate/promote and utilities.
- `configs/`: runtime, safety, mining, server, platform profiles.
- `outputs/`: checkpoints, reports, registry, ONNX artifacts.
- `inference_server/`: FastAPI serving stack.
- `lidar_perception/`: core model/data/evaluation code.
- `app/`: landing site (Next.js).
- `tests/`: unit/integration tests.
- `mlruns/`: MLflow tracking artifacts.

## 4. GitHub Actions CI/CD Flow

```mermaid
flowchart TD
  P[push/PR] --> L[lint-and-test]
  L --> E[evaluate-on-push]
  L --> S[smoke-train main]
  S --> O[onnx export+validate]
  E --> R[safety gate report artifact]
```

## 5. MLflow Tracking Integration

```mermaid
flowchart LR
  T[train/retrain/evaluate scripts] --> M[MLflowTracker]
  M --> U[mlruns tracking_uri]
  U --> V[experiment history + artifacts]
```

## 6. Safety Gate Decision Flow

```mermaid
flowchart TD
  C[candidate eval_report] --> G[safety_gate.py]
  P[production eval_report optional] --> G
  S[safety_policy.yaml] --> G
  G -->|PASS/WARN| X[eligible for compare/promote]
  G -->|BLOCK| Y[reject candidate + investigate]
```
