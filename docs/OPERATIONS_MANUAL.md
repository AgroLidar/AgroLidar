# Operations Manual

## 1. Startup Sequence
```bash
make registry-status
make serve
```
Optional validation:
```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/metrics
```

## 2. Normal Operating Workflow
1. Verify health endpoint status.
2. Stream BEV frames into `/predict` or `/predict/batch`.
3. Consume response risk fields in HMI/control system.
4. Log all critical events and retain payload metadata.

## 3. Operator Pre-use Checks
- Mount and cable integrity.
- Lens/window cleanliness.
- Compute enclosure temperature and fan health.
- `/health` responds and model is loaded.

## 4. Output Interpretation
`PredictionResponse` includes:
- `detections[]`
- `inference_time_ms`
- `model_version`
- `dangerous_objects`
- `collision_risk` (`high` / `medium` / `low` / `none`)

Per-detection `risk_level` values:
- `critical`
- `warning`
- `safe`

## 5. Hazard Handling Guidance
- `collision_risk=high`: stop operation, inspect scene and sensors.
- `collision_risk=medium`: reduce speed and alert operator.
- `collision_risk=low/none`: continue with standard monitoring.

## 6. Stop-and-Inspect Conditions
- Persistent unhealthy `/health`.
- Repeated high-risk triggers in clear environments.
- Sudden latency jumps or missing frames.

## 7. Maintenance Cadence
- Daily: health check + critical log review.
- Weekly: run hard-case mining and refresh review queue.
- Monthly: retrain candidate, run safety gate, compare/promote only if passed.

## 8. Log Retention and Rotation
- Keep operational logs and reports in `outputs/reports/`.
- Archive registry history (`outputs/registry/registry.json`) before promotions.

## 9. Backup Procedures
- Backup `outputs/checkpoints/`, `outputs/registry/`, and `outputs/reports/`.
- Backup `configs/` and `.env` deployment values.

## 10. Pilot Workflow (Recommended)
- Daily: `GET /health`, review CRITICAL log entries.
- Weekly: `python scripts/mine_hard_cases.py` then `python scripts/build_review_queue.py`.
- Monthly: `make retrain && make evaluate && make safety-check && make compare` and promote if policy passes.
