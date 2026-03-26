# AgroLidar

Production-oriented PyTorch baseline for LiDAR obstacle detection on tractors and agricultural machines operating in difficult field conditions.

## Features

- Obstacle detection for `human`, `animal`, `vehicle`, `post`, and `rock`
- BEV semantic segmentation tuned for unstructured field environments
- Distance estimation and safety-oriented hazard scoring
- Terrain-normalized preprocessing and conservative atmospheric denoising
- Robustness augmentations for dust, rain, low visibility, sparse returns, and partial occlusion
- Modular architecture with swappable models and API-ready serving
- Temporal tracking to stabilize detections across consecutive tractor frames
- Velocity estimation, stop-zone prediction, and temporal occupancy fusion for sequence-aware safety
- Synthetic agricultural scenario generator for MVP demos before field data arrives
- Support for `.bin` and `.pcd` point cloud loading
- Checkpointing, logging, evaluation, and visualization
- FastAPI starter for future vehicle or edge integration

## Project Structure

```text
lidar_perception/
  data/
  models/
  training/
  inference/
  simulation/
  evaluation/
  api/
  utils/
configs/
notebooks/
scripts/
```

## Architecture

The default model is a PointPillars-inspired Bird's Eye View pipeline adapted for agricultural obstacle detection:

1. Raw point clouds are cropped to a configurable range.
2. Agricultural preprocessing estimates local ground, normalizes terrain, and removes likely airborne noise.
3. Points are voxelized into a BEV feature grid.
4. A CNN backbone extracts spatial features.
4. Three task heads run on shared features:
   - Detection head: class heatmaps, box offsets, sizes, yaw, confidence
   - Segmentation head: semantic logits per BEV cell
   - Obstacle head: occupancy and distance regression
5. Inference produces detections, nearest-obstacle distance, and a hazard score for startup-style safety logic.
6. A lightweight temporal tracker smooths detections and estimates per-track velocity.
7. The runtime fuses occupancy across short windows and computes tractor stop-zone risk from vehicle speed.

This design is practical for tractors because BEV convolution is efficient on edge GPUs and does not rely on lane structure or dense urban priors.

## How This Differs From Urban AV Systems

- The scene model assumes irregular terrain and unstructured drivable space rather than lanes or clean roads.
- Vegetation and uneven ground are treated as persistent nuisance factors, so the synthetic pipeline injects crop clutter, ground undulation, and degraded sensing.
- Safety prioritizes missed detections of people, animals, rocks, and posts over appearance-heavy classification.
- Hazard scoring is included in the MVP because agricultural operators need actionable alerts, not just raw boxes.
- Inference favors forward travel-corridor risk, which matches how tractors actually need to decide when to slow or stop.

## Innovation Layer

1. Hazard-aware obstacle ranking
   Why it matters:
   A tractor should stop for a person at medium confidence sooner than for tall grass at high confidence.
   How to implement:
   The MVP already computes a hazard score from class priority, confidence, and distance. In V2 this can become a learned risk model tied to stopping distance and implement speed.
   Stage:
   MVP now, learned version in V2.

2. Adaptive dust and rain filtering
   Why it matters:
   Agricultural LiDAR often suffers from sparse returns and backscatter in dusty or rainy work.
   How to implement:
   The MVP simulates attenuation, point dropout, intensity perturbation, and partial occlusion. V2 should add temporal filtering and return-consistency gating across short windows.
   Stage:
   MVP augmentations now, temporal filter in V2.

3. Terrain-aware obstacle reasoning
   Why it matters:
   Uneven ground and ruts can look like obstacles if the model assumes flat roads.
   How to implement:
   The synthetic generator creates rolling terrain; V2 should explicitly estimate local ground planes and fuse them into the obstacle head.
   Stage:
   MVP-ready hooks now, stronger module in V2.

Additional roadmap ideas:

- Camera fusion for operator-assist views and ambiguous obstacle verification
- Self-supervised field adaptation per farm, season, or crop type
- INT8 TensorRT deployment profile for Jetson/Orin edge compute

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Train

```bash
python scripts/train.py --config configs/base.yaml
```

## Evaluate

```bash
python scripts/evaluate.py --config configs/base.yaml --checkpoint outputs/checkpoints/best.pt
```

## Inference

Run on a synthetic agricultural sample:

```bash
python scripts/infer.py --config configs/base.yaml --checkpoint outputs/checkpoints/best.pt --sample-index 0
```

Run on a short synthetic sequence to see stabilized tracking:

```bash
python scripts/infer.py --config configs/base.yaml --checkpoint outputs/checkpoints/best.pt --sample-index 0 --sequence-length 3
```

Add tractor speed for stop-zone and TTC logic:

```bash
python scripts/infer.py --config configs/base.yaml --checkpoint outputs/checkpoints/best.pt --sample-index 0 --sequence-length 5 --tractor-speed-mps 3.5
```

Run on a real point cloud:

```bash
python scripts/infer.py --config configs/base.yaml --checkpoint outputs/checkpoints/best.pt --point-cloud /path/to/frame.bin
```

Run a demo sequence:

```bash
python scripts/demo.py --config configs/base.yaml --checkpoint outputs/checkpoints/best.pt --num-scenes 3
```

Start the API:

```bash
uvicorn lidar_perception.api.main:app --reload
```

Reset tracker state in the API:

```bash
curl -X POST "http://127.0.0.1:8000/tracking/reset"
```

## Web Demo

Run the interactive web demo:

```bash
cd /Users/geromendez/Dev/AgroLidar
PYTHONPATH=/Users/geromendez/Dev/AgroLidar ./.venv/bin/python -m uvicorn lidar_perception.api.main:app --host 127.0.0.1 --port 8010
```

Then open:

```text
http://127.0.0.1:8010/
```

The web demo lets you:

- advance synthetic LiDAR frames
- reset the tracked sequence
- change tractor speed
- inspect tracks, TTC, stop zone, hazard level, and temporal fusion

## Data

### Synthetic

The default configuration uses an agricultural scene simulator with:

- rolling terrain
- vegetation clutter
- posts, rocks, humans, animals, and vehicles
- dust/rain/low-visibility approximations

### Real datasets

You can adapt the folder layout to datasets such as KITTI, nuScenes, and Waymo for initial pretraining, then fine-tune on tractor-collected field data:

- `.bin`: KITTI style `float32` `[x, y, z, intensity]`
- `.pcd`: Open3D-compatible point cloud files

For production integration, create dataset adapters that emit the same sample dictionary used by the training code. This lets road data bootstrap the detector while preserving a clean path to agricultural domain adaptation.

## Evaluation Priorities

The evaluation pipeline reports:

- `mAP`
- segmentation IoU
- obstacle distance MAE
- precision / recall
- false negative rate for dangerous classes
- latency and average inference time
- robustness under simulated noisy conditions

## Real Agro Upgrades In This Version

- Local ground estimation for uneven terrain so the model sees relative obstacle height rather than raw height.
- Conservative denoising for likely dust/rain backscatter and other sparse airborne returns.
- Travel-corridor-aware hazard scoring with `monitor`, `warning`, and `emergency` risk levels.
- Short-horizon track IDs and smoothing so obstacle alerts do not flicker across consecutive frames.
- Per-track velocity, time-to-collision, and stop-zone occupancy based on tractor speed.
- Temporal occupancy fusion across 3-10 frames to reduce flicker from sparse or degraded LiDAR returns.
- Filtered-vs-raw visualization to inspect whether preprocessing is helping or hiding useful structure.

## Deployment Recommendations

### Edge deployment on tractor

- Export the model with TorchScript or ONNX
- Optimize with TensorRT for Jetson / Orin-class hardware
- Run inference inside a ROS2, CAN-integrated, or gRPC microservice with pinned-memory batching and watchdogs
- Keep latency bounded and fail safe on degraded confidence
- Log low-confidence or anomalous predictions for safety review

### Cloud training pipeline

- Store raw point clouds, environmental metadata, and field labels in object storage
- Use distributed PyTorch training on GPU nodes
- Version configs, checkpoints, and metrics through MLflow or Weights & Biases
- Run scheduled regression suites on held-out weather, crop, and terrain slices

## Next Steps For Real Agricultural Data

- Add a dataset adapter for tractor-mounted LiDAR logs with calibration metadata
- Record weather and implement state during collection for robustness slicing
- Add temporal tracking to stabilize detections over bumps and sparse returns
- Tune the hazard score against tractor stopping distance and operator feedback
- Quantize and benchmark on the target edge computer

## Notes

- The included detector is a strong startup-MVP scaffold, not a benchmark-tuned production release.
- For commercial deployment, pair this with field calibration workflows, safety case documentation, and a real agricultural validation campaign.
