# Usage Guide

## Common commands

```bash
# baseline train
python scripts/train.py --config configs/train.yaml

# candidate retrain with hard-case strategy
python scripts/retrain.py --config configs/retrain.yaml

# evaluate current checkpoint
python scripts/evaluate.py --config configs/base.yaml

# compare candidate and production
python scripts/compare_models.py \
  --production-metrics outputs/reports/production_eval.json \
  --candidate-metrics outputs/reports/eval_report.json

# run safety gate
python scripts/safety_gate.py \
  --candidate-report outputs/reports/eval_report.json \
  --production-report outputs/reports/production_eval.json \
  --output outputs/reports/gate_report.json
```

## Inference server

```bash
uvicorn inference_server.main:app --host 0.0.0.0 --port 8000
```

Health endpoint: `GET /health`
Prediction endpoint: `POST /predict`

## ONNX export and validation

```bash
python scripts/export_onnx.py --validate --benchmark
python scripts/validate_onnx.py --onnx-path outputs/onnx/model.onnx --checkpoint outputs/checkpoints/best.pt
```

## Pipeline automation

```bash
make pipeline
```

This runs train/retrain/evaluate/safety-check/compare/promote in sequence for controlled local validation.
