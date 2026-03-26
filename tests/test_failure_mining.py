from lidar_perception.evaluation.failure_mining import identify_failures


def test_failure_mining_reasons():
    result = {
        "nearest_obstacle_distance_m": 2.0,
        "detections": [
            {"score": 0.2, "track_status": "tentative", "hazard_score": 0.6, "distance_m": 3.0, "risk_level": "warning", "label_name": "human"}
        ],
    }
    reasons = identify_failures(result, {"low_confidence": 0.25, "near_miss_distance_m": 5.0, "distance_error_m": 1.0}, gt={"expected_min_distance_m": 10.0})
    assert "low_confidence" in reasons
    assert "tracking_inconsistent" in reasons
    assert "near_miss_hazard" in reasons
    assert "distance_disagreement" in reasons
