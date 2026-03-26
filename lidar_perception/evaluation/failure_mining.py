from __future__ import annotations


def identify_failures(result: dict, thresholds: dict, gt: dict | None = None) -> list[str]:
    reasons: list[str] = []
    detections = result.get("detections", [])
    if not detections:
        reasons.append("empty_prediction")
        return reasons

    low_conf = [d for d in detections if d.get("score", 1.0) < thresholds.get("low_confidence", 0.25)]
    if low_conf:
        reasons.append("low_confidence")

    inconsistent = [d for d in detections if d.get("track_status") == "tentative" and d.get("hazard_score", 0.0) > 0.4]
    if inconsistent:
        reasons.append("tracking_inconsistent")

    near_miss = [d for d in detections if d.get("distance_m", 999.0) < thresholds.get("near_miss_distance_m", 7.0) and d.get("risk_level") != "emergency"]
    if near_miss:
        reasons.append("near_miss_hazard")

    dangerous_miss = [d for d in detections if d.get("label_name") in {"human", "animal"} and d.get("score", 1.0) < 0.35]
    if dangerous_miss:
        reasons.append("dangerous_class_low_confidence")

    if gt and gt.get("expected_min_distance_m") is not None:
        expected = float(gt["expected_min_distance_m"])
        actual = float(result.get("nearest_obstacle_distance_m", expected))
        if abs(actual - expected) > thresholds.get("distance_error_m", 5.0):
            reasons.append("distance_disagreement")

    return reasons
