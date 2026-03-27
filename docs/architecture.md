# Architecture

AgroLidar is organized as a modular pipeline and runtime system.

## High-level pipeline

1. Data generation/collection
2. Model training or retraining
3. Safety-oriented evaluation
4. Candidate vs production comparison
5. Policy gate and promotion
6. Inference deployment

## Component map

- `lidar_perception/data`: ingestion, dataset definitions, augmentation, preprocessing
- `lidar_perception/models`: backbones, detection heads, model assembly
- `lidar_perception/training`: engine, losses, metrics
- `lidar_perception/evaluation`: robustness and comparative evaluations
- `lidar_perception/registry`: model lifecycle tracking and promotion status
- `inference_server`: API serving, request models, predictor middleware

## Registry lifecycle

Candidate models are produced under `outputs/candidates/` and compared against production references. Promotion outcomes are stored in `outputs/registry/registry.json` with explicit state transitions (`accepted`, `rejected`, `archived`).

## Safety model governance

Safety checks are codified in:

- `scripts/safety_gate.py`
- `configs/safety_policy.yaml`

This prevents accidental promotion of regressed models in dangerous classes.
