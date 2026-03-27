# Sensor Calibration

## Why Calibration Matters
AgroLidar consumes BEV tensors. Any misalignment between physical sensor pose and assumed transform degrades projection quality and can increase false negatives in safety classes.

## Intrinsic Calibration
LiDAR vendors typically provide:
- Beam elevation/azimuth pattern.
- Range accuracy/error envelope.
- Intensity normalization behavior.

Validate vendor intrinsic calibration status before field deployment.

## Extrinsic Calibration
Define sensor pose relative to vehicle reference frame:
- mounting height (m)
- forward offset (m)
- lateral offset (m)
- pitch/roll/yaw (deg)

These are captured operationally via platform profiles (`configs/platforms/*.yaml`) and should be mapped into your BEV projection transform.

## Mapping to AgroLidar BEV Projection
- `configs/base.yaml` defines BEV dimensions/channels and point cloud range.
- `docs/DATA_SCHEMA.md` defines final BEV tensor contract.
- Platform profile geometry values are the recommended source for mounting transform parameters in your ingest/projection layer.

## Ground Plane Estimation Checks
- On flat ground, confirm near-ground objects project consistently frame-to-frame.
- Check horizon line drift and object distance stability.
- Verify no systematic near-field clipping from excessive negative pitch.

## Recommended Field Procedures
- Use known-distance markers (e.g., 5 m, 10 m, 20 m stakes).
- Use flat-ground scan passes to verify stable ground projection.
- Optional checkerboard/board targets for repeated geometric sanity checks.

## Calibration Quality Validation
1. Generate controlled synthetic data:
```bash
python scripts/generate_synthetic_data.py --train-samples 20 --val-samples 5
```
2. Run evaluation and inspect distance error proxies:
```bash
python scripts/evaluate.py --config configs/base.yaml
```
3. Compare BEV visualizations and distance metrics over time.

Use `distance_error` metrics in evaluation reports as a practical drift proxy.

## Re-calibration Triggers
- Physical impact or mount adjustment.
- Seasonal thermal extremes.
- Evaluation trend regression in distance error.

## Calibration Logging Recommendation
Store calibration logs in `outputs/reports/` with timestamps and vehicle IDs to support audit trails and maintenance history.

## Data Contract Reference
See `docs/DATA_SCHEMA.md` for frame format requirements.
