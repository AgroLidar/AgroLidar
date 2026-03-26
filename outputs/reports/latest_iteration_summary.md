# Iteration Summary (2026-03-26)

## What was implemented
- Strengthened failure mining with **ground-truth-aware dangerous miss detection**, **distance anomaly checks**, and **cross-frame tracking instability detection**.
- Extended hard-case mining script to accept optional `--gt-manifest`, consume configurable failure thresholds, and persist GT context in hard-case records.
- Upgraded model comparison policy to enforce dangerous-class recall safeguards and emit policy details in reports.
- Added markdown report generation for model comparison at `outputs/reports/model_comparison.md`.
- Fixed NumPy 2.x compatibility in AP integration (`np.trapezoid`), unblocking training/evaluation smoke runs.
- Corrected broken `base_config` references in YAML files that prevented config inheritance resolution.
- Added regression tests for new failure-mining and model-comparison behaviors.

## What improved
- Failure collection now captures richer safety-critical failure modes and supports offline GT auditing.
- Promotion logic now guards against regressions in dangerous subclasses even when aggregate recall improves.
- Model comparison outputs are now human-readable for review workflows.
- Training/evaluation scripts run successfully in the current environment after metrics fix.

## What still fails / limitations
- Active-learning mining with `configs/active_learning.yaml` still requires checkpoint architecture compatibility; demo checkpoint from `configs/demo_quick.yaml` is not shape-compatible with base model settings.
- Latency and perception metrics are currently synthetic-data based; no real tractor logs were exercised.
- No formal lint/type-check toolchain is configured in-repo.

## Risks / assumptions
- GT manifest format for hard-case mining assumes JSONL entries keyed by `sample_id`, with optional `dangerous_objects` and `expected_min_distance_m`.
- Cross-frame instability currently uses distance-jump heuristic without ego-motion compensation.
- Comparison policy assumes per-class recall fields exist as `recall_<class>`; it falls back to global recall if absent.

## Metrics / validation snapshot
- `pytest`: 10/10 passing.
- Training smoke (`configs/demo_quick.yaml`) completed 1 epoch and checkpointed.
- Inference smoke generated sequence predictions with structured JSON outputs.
- Evaluation smoke generated report metrics.
- Hard-case mining and review queue scripts executed successfully with demo config.
- Model comparison generated JSON + markdown reports.
