# Next Iteration Prompt

## Current repo state
The platform now has end-to-end scripts for training, evaluation, inference, hard-case mining, review queue generation, retraining entrypoint, model comparison, and model registry scaffolding. Failure mining now supports GT-aware missed-dangerous detection and sequence instability checks. Model comparison now enforces dangerous-class recall protection and produces markdown reports.

## Incomplete areas (highest priority)
1. **Realistic evaluation depth**
   - Add per-class precision/recall tables and hazard calibration analysis.
   - Add robustness slices by environment metadata (dust/rain/night/terrain).
2. **Retraining data composition**
   - Implement actual dataset mixing of reviewed hard cases with weighting/oversampling (currently metadata only).
3. **Registry lifecycle automation**
   - Add promotion/archival transaction script with policy gate + atomic registry updates.
4. **Inference/failure integration**
   - Persist unified inference event logs (frame-level + track-level) to make post-hoc mining deterministic.

## Biggest weaknesses
- Synthetic-only validation does not prove field robustness.
- Retraining pipeline does not yet consume reviewed queue artifacts into dataloaders.
- No linter/type checker gates in CI-like validation.

## Exact next actions
1. Implement `ReviewedHardCaseDataset` and `CompositeTrainingDataset` in `lidar_perception/data/datasets.py`.
2. Update `scripts/retrain.py` + train entrypoint to build mixed dataset from `data/review_queue/manifest.jsonl` with oversampling ratio.
3. Extend `Trainer.evaluate()` outputs with dangerous per-class recall metrics.
4. Add tests for dataset mixing and per-class metric computation.
5. Add `scripts/promote_model.py` to apply comparison policy and update registry statuses.

## Commands to run
- `pytest -q`
- `python scripts/train.py --config configs/demo_quick.yaml`
- `python scripts/retrain.py --config configs/retrain.yaml --resume outputs/checkpoints/latest.pt`
- `python scripts/evaluate.py --config configs/eval.yaml --checkpoint outputs/checkpoints/best.pt`
- `python scripts/compare_models.py --production-metrics outputs/reports/production_eval.json --candidate-metrics outputs/reports/eval_report.json --config configs/eval.yaml`

## Quality expectations
- No placeholder logic; wire new datasets into real training flow.
- Backward-compatible configs.
- All added scripts must be idempotent and produce deterministic artifacts.
- Add tests that fail without the implemented logic.

## Constraints
- Do **not** redo existing failure-mining and comparison-report improvements.
- Do **not** introduce online learning in inference runtime.
- Preserve safety-first promotion criteria (dangerous recall + FNR + latency guardrails).
