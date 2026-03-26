from __future__ import annotations


def compare_models(production: dict, candidate: dict, cfg: dict | None = None) -> dict:
    cfg = cfg or {}
    latency_tolerance = float(cfg.get("max_latency_regression_ms", 4.0))
    recall_gain_needed = float(cfg.get("min_recall_gain", 0.01))
    fnr_drop_needed = float(cfg.get("min_fnr_drop", 0.01))
    max_robustness_gap_regression = float(cfg.get("max_robustness_gap_regression", 0.02))

    recall_gain = float(candidate.get("recall", 0.0) - production.get("recall", 0.0))
    fnr_drop = float(production.get("dangerous_fnr", 1.0) - candidate.get("dangerous_fnr", 1.0))
    latency_regression = float(candidate.get("latency_ms", 1e9) - production.get("latency_ms", 0.0))
    distance_mae_delta = float(candidate.get("distance_mae", 1e9) - production.get("distance_mae", 1e9))
    robustness_gap_regression = float(candidate.get("robustness_gap", production.get("robustness_gap", 0.0)) - production.get("robustness_gap", 0.0))

    dangerous_classes = cfg.get("dangerous_classes", ["human", "animal", "rock", "post"])
    per_class_delta: dict[str, float] = {}
    per_class_pass = True
    min_per_class_gain = float(cfg.get("min_dangerous_class_recall_gain", 0.0))

    for cls_name in dangerous_classes:
        key = f"recall_{cls_name}"
        prod_cls = float(production.get(key, production.get("recall", 0.0)))
        cand_cls = float(candidate.get(key, candidate.get("recall", 0.0)))
        delta = cand_cls - prod_cls
        per_class_delta[cls_name] = delta
        if delta < min_per_class_gain:
            per_class_pass = False

    promote = (
        recall_gain >= recall_gain_needed
        and fnr_drop >= fnr_drop_needed
        and distance_mae_delta <= 0.0
        and latency_regression <= latency_tolerance
        and robustness_gap_regression <= max_robustness_gap_regression
        and per_class_pass
    )
    return {
        "production": production,
        "candidate": candidate,
        "policy": {
            "max_latency_regression_ms": latency_tolerance,
            "min_recall_gain": recall_gain_needed,
            "min_fnr_drop": fnr_drop_needed,
            "max_robustness_gap_regression": max_robustness_gap_regression,
            "dangerous_classes": dangerous_classes,
            "min_dangerous_class_recall_gain": min_per_class_gain,
        },
        "deltas": {
            "recall_gain": recall_gain,
            "dangerous_fnr_drop": fnr_drop,
            "latency_regression_ms": latency_regression,
            "distance_mae_delta": distance_mae_delta,
            "robustness_gap_regression": robustness_gap_regression,
            "dangerous_class_recall_delta": per_class_delta,
        },
        "promote": bool(promote),
        "decision_reason": "candidate_improves_safety_without_major_latency_regression" if promote else "candidate_does_not_meet_promotion_policy",
    }
