from __future__ import annotations


def _detect_dangerous_miss_from_gt(result: dict, gt: dict | None) -> bool:
    if not gt:
        return False
    dangerous_gt = gt.get("dangerous_objects")
    if not dangerous_gt:
        return False

    detections = result.get("detections", [])
    detected_classes = {str(d.get("label_name", "")).lower() for d in detections}
    for item in dangerous_gt:
        label = str(item.get("label_name", "")).lower()
        if label and label not in detected_classes:
            return True
    return False


def _detect_distance_anomaly(result: dict, gt: dict | None, thresholds: dict) -> bool:
    if not gt or gt.get("expected_min_distance_m") is None:
        return False
    expected = float(gt["expected_min_distance_m"])
    actual = float(result.get("nearest_obstacle_distance_m", expected))
    return abs(actual - expected) > float(thresholds.get("distance_error_m", 5.0))


def _detect_sequence_instability(result: dict, previous_result: dict | None, thresholds: dict) -> bool:
    if not previous_result:
        return False

    prev_by_track = {
        int(d.get("track_id")): d
        for d in previous_result.get("detections", [])
        if d.get("track_id") is not None
    }
    if not prev_by_track:
        return False

    jump_threshold = float(thresholds.get("track_distance_jump_m", 6.0))
    for det in result.get("detections", []):
        track_id = det.get("track_id")
        if track_id is None:
            continue
        prior = prev_by_track.get(int(track_id))
        if not prior:
            continue
        current_distance = float(det.get("distance_m", 0.0))
        previous_distance = float(prior.get("distance_m", current_distance))
        if abs(current_distance - previous_distance) > jump_threshold:
            return True
    return False


def identify_failures(result: dict, thresholds: dict, gt: dict | None = None, previous_result: dict | None = None) -> list[str]:
    reasons: list[str] = []
    detections = result.get("detections", [])
    if not detections:
        reasons.append("empty_prediction")
        return reasons

    low_conf = [d for d in detections if d.get("score", 1.0) < thresholds.get("low_confidence", 0.25)]
    if low_conf:
        reasons.append("low_confidence")

    inconsistent = [d for d in detections if d.get("track_status") == "tentative" and d.get("hazard_score", 0.0) > 0.4]
    if inconsistent or _detect_sequence_instability(result, previous_result, thresholds):
        reasons.append("tracking_inconsistent")

    near_miss = [
        d for d in detections if d.get("distance_m", 999.0) < thresholds.get("near_miss_distance_m", 7.0) and d.get("risk_level") != "emergency"
    ]
    if near_miss:
        reasons.append("near_miss_hazard")

    dangerous_low_conf = [d for d in detections if d.get("label_name") in {"human", "animal"} and d.get("score", 1.0) < 0.35]
    if dangerous_low_conf:
        reasons.append("dangerous_class_low_confidence")

    if _detect_dangerous_miss_from_gt(result, gt):
        reasons.append("missed_dangerous_object")

    if _detect_distance_anomaly(result, gt, thresholds):
        reasons.append("distance_disagreement")

    return reasons
