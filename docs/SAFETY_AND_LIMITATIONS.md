# Safety and Limitations

## 1. System Boundaries
AgroLidar is a **perception system** that outputs detections and risk levels. It is **not** a complete safety system and does not directly provide braking, supervisory control, or certified safety actuation.

## 2. Training and Promotion Policy
- No online self-training in production.
- Offline retraining plus controlled promotion via safety gate only.
- Policy source: `configs/safety_policy.yaml`.

## 3. Safety Gate Hard Limits
Current policy defaults:
- `dangerous_fnr_hard_limit: 0.10`
- `human_recall_minimum: 0.90`

Candidates failing blocking rules must not be promoted.

## 4. Degrading Conditions
Performance can degrade due to:
- heavy dust, rain, and mud contamination
- wet vegetation and specular reflections
- strong sunlight and thermal stress
- poor mounting geometry or loose brackets
- occlusions by implements/attachments
- sparse returns near sensor range extremes
- compute thermal throttling and power instability

## 5. Operator Responsibility
Operators and integrators remain responsible for safe machine operation and for configuring downstream alerting/control systems.

## 6. Fail-safe Integration Expectations
- Implement watchdog polling on `/health`.
- Treat unhealthy/degraded responses and HTTP 503 as degraded perception state.
- "No inference" is **not** equivalent to "no hazard".

## 7. Pilot vs Production Caveat
This repository supports prototype/pilot workflows. Production deployment requires additional validation, cybersecurity hardening, and jurisdiction-specific compliance testing.

## 8. Synthetic Data Limitation
Current pipeline includes synthetic training/evaluation assets. Real field performance must be validated with representative real LiDAR captures before production use.

## 9. Recommended Minimum Testing Before Pilot Go-live
- Multi-day representative field capture in expected environmental conditions.
- Safety-class recall/FNR trend review per crop/season context.
- End-to-end latency and failover behavior tests under load.
