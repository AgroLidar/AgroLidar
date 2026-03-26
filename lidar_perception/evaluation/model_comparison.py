from __future__ import annotations


SAFETY_METRICS = ["recall", "dangerous_fnr", "distance_mae"]


def compare_models(production: dict, candidate: dict, cfg: dict | None = None) -> dict:
    cfg = cfg or {}
    latency_tolerance = float(cfg.get("max_latency_regression_ms", 4.0))
    recall_gain_needed = float(cfg.get("min_recall_gain", 0.01))
    fnr_drop_needed = float(cfg.get("min_fnr_drop", 0.01))

    recall_gain = candidate.get("recall", 0.0) - production.get("recall", 0.0)
    fnr_drop = production.get("dangerous_fnr", 1.0) - candidate.get("dangerous_fnr", 1.0)
    latency_regression = candidate.get("latency_ms", 1e9) - production.get("latency_ms", 0.0)

    promote = (
        recall_gain >= recall_gain_needed
        and fnr_drop >= fnr_drop_needed
        and candidate.get("distance_mae", 1e9) <= production.get("distance_mae", 1e9)
        and latency_regression <= latency_tolerance
    )
    return {
        "production": production,
        "candidate": candidate,
        "deltas": {
            "recall_gain": recall_gain,
            "dangerous_fnr_drop": fnr_drop,
            "latency_regression_ms": latency_regression,
            "distance_mae_delta": candidate.get("distance_mae", 1e9) - production.get("distance_mae", 1e9),
        },
        "promote": bool(promote),
        "decision_reason": "candidate_improves_safety_without_major_latency_regression" if promote else "candidate_does_not_meet_promotion_policy",
    }
