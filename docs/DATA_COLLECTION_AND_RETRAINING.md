# Data Collection and Retraining

## 1. Structured Logging
Use inference-server logs and `outputs/reports/` artifacts as primary field evidence.

## 2. Hard-case Mining
Run:
```bash
python scripts/mine_hard_cases.py --inference-dir outputs/inference/
```
Mining behavior is controlled in `configs/mining.yaml`.

## 3. Build Review Queue
```bash
python scripts/build_review_queue.py
```
This creates/updates `data/review_queue/queue.json` and summary markdown.

## 4. Human Review Process
`reviewed=true` means a designated reviewer validated/annotated cases for training inclusion. Review ownership should be explicitly assigned per deployment.

## 5. Offline Retraining
```bash
python scripts/retrain.py --config configs/retrain.yaml
```
Retraining writes candidate artifacts under `outputs/candidates/<run>/`.

## 6. Safety Gate
```bash
python scripts/safety_gate.py --candidate-report outputs/reports/eval_report.json --production-report outputs/reports/production_eval.json --output outputs/reports/gate_report.json
```
Unsafe candidates are blocked.

## 7. Promotion
```bash
python scripts/promote_model.py --candidate-model outputs/candidates/latest/checkpoints/best.pt --production-model outputs/checkpoints/best.pt --comparison-report outputs/reports/model_comparison.json
```
Registry tracked in `outputs/registry/registry.json`.

## 8. Why No Online Learning
Online self-training can introduce unreviewed regressions and violates controlled safety policy.

## 9. Recommended Pilot Cadence
- Daily: review logs and critical events.
- Weekly: mine hard cases + build review queue.
- Monthly: retrain + evaluate + safety gate + compare + promote if passed.

## 10. MLflow and Regression Tracking
- Launch tracking UI: `make mlflow-ui`
- Generate regression view: `make regression-report`
