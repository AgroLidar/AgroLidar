# Iteration Summary (Hard-Case Learning + Promotion Controls)

## What was implemented

- Added `ReviewedHardCaseDataset` for loading hard cases from `data/hard_cases/` and `data/review_queue/` with JSON/JSONL/CSV manifest support.
- Added `CompositeTrainingDataset` to mix base and hard-case samples with configurable ratio plus hazard/uncertainty weighting and optional dangerous-class oversampling.
- Upgraded retraining pipeline (`scripts/retrain.py`) to build candidate-only runs, log hard-case usage and class distribution, and persist composition metadata.
- Upgraded evaluation pipeline to emit safety-critical per-class metrics and dangerous-class aggregate score in JSON + Markdown.
- Added `scripts/promote_model.py` for registry-aware model promotion/rejection decisions.
- Strengthened model comparison policy with robustness regression constraints.
- Added tests for hard-case datasets, retrain integration, and promotion logic.

## Dataset integration results

- Retraining read hard-case sources and produced a compositional dataset summary.
- Current run had `hard_cases_used=0` (no reviewed hard labels present in repo data directories), so candidate was trained from base-only samples with the configured composite logic active.
- Composition captured in `outputs/reports/retrain_metadata.json`.

## Retraining behavior

- Generated a new candidate model run at:
  - `outputs/candidates/retrain_candidate_20260326T200355Z`
- Production checkpoint path was not overwritten.
- Candidate evaluation report generated at:
  - `outputs/reports/eval_report.json`
  - `outputs/reports/eval_report.md`

## Metric outcomes / promotion decision

- Candidate dangerous-class recall remained poor (`human/animal/rock/post` recall = `0.0` in this run).
- `scripts/compare_models.py` returned `promote=false` due to safety and latency policy failures.
- `scripts/promote_model.py` marked candidate as `rejected` in `outputs/registry/registry.json`.

## Risks and gaps

1. **Real reviewed hard cases are still missing** in local data folders, so retraining cannot yet improve dangerous-class recall.
2. Candidate latency is far above production baseline in this run.
3. Current synthetic-heavy training still underperforms safety-critical targets; next iteration must integrate reviewed real-world annotations.
