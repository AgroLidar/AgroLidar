# Next Iteration Prompt — AgroLidar

## Current repo state

AgroLidar now has:

- hard-case dataset integration (`ReviewedHardCaseDataset`, `CompositeTrainingDataset`)
- retraining pipeline using base + hard-case composition
- safety-critical per-class evaluation metrics + dangerous aggregate score
- policy-driven model promotion/rejection script with registry transitions

Validation commands pass and outputs are generated:

- `pytest`
- `python scripts/retrain.py --config configs/base.yaml`
- `python scripts/evaluate.py --config configs/base.yaml`
- `python scripts/compare_models.py --production-metrics outputs/reports/production_eval.json --candidate-metrics outputs/reports/eval_report.json --config configs/eval.yaml --output outputs/reports/model_comparison.json --output-md outputs/reports/model_comparison.md`
- `python scripts/promote_model.py --candidate-model outputs/candidates/retrain_candidate_20260326T200355Z/checkpoints/best.pt --production-model outputs/checkpoints/best.pt --comparison-report outputs/reports/model_comparison.json`

## Biggest weaknesses (focus)

1. **No reviewed real-world hard-case labels in training input yet** (hard-case count stayed zero).
2. Safety recall for dangerous classes is still insufficient.
3. Latency/stability optimization for candidate models remains weak.

## Top priorities for next iteration (very important: real-world dataset integration)

1. Add real reviewed hard-case annotations and enforce schema validation.
2. Create a robust reviewed-data ingestion pipeline (label QA checks, manifest audits, split controls).
3. Add retraining curriculum controls (stage-in hard cases, adaptive ratio by class deficiency).
4. Add automated regression gates for dangerous-class recall and latency before candidate export.
5. Improve model/feature efficiency to reduce latency without dropping safety recall.

## Constraints

- Do not implement online self-training.
- Do not remove existing systems.
- Keep candidate-vs-production separation strict.
- Keep outputs machine-readable and reproducible.

## Suggested commands

```bash
pytest
python scripts/retrain.py --config configs/retrain.yaml
python scripts/evaluate.py --config configs/base.yaml
python scripts/compare_models.py --production-metrics outputs/reports/production_eval.json --candidate-metrics outputs/reports/eval_report.json --config configs/eval.yaml --output outputs/reports/model_comparison.json --output-md outputs/reports/model_comparison.md
python scripts/promote_model.py --candidate-model <candidate_ckpt> --production-model <production_ckpt> --comparison-report outputs/reports/model_comparison.json
```
