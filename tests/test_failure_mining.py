from lidar_perception.evaluation.failure_mining import identify_failures


def test_failure_mining_reasons():
    result = {
        "nearest_obstacle_distance_m": 2.0,
        "detections": [
            {
                "score": 0.2,
                "track_status": "tentative",
                "hazard_score": 0.6,
                "distance_m": 3.0,
                "risk_level": "warning",
                "label_name": "human",
            }
        ],
    }
    reasons = identify_failures(
        result,
        {"low_confidence": 0.25, "near_miss_distance_m": 5.0, "distance_error_m": 1.0},
        gt={"expected_min_distance_m": 10.0},
    )
    assert "low_confidence" in reasons
    assert "tracking_inconsistent" in reasons
    assert "near_miss_hazard" in reasons
    assert "distance_disagreement" in reasons


def test_failure_mining_detects_missed_dangerous_object_and_track_jump():
    previous = {
        "detections": [
            {
                "track_id": 7,
                "distance_m": 4.0,
                "label_name": "human",
                "score": 0.9,
                "risk_level": "warning",
            }
        ]
    }
    current = {
        "nearest_obstacle_distance_m": 20.0,
        "detections": [
            {
                "track_id": 7,
                "distance_m": 13.5,
                "label_name": "vehicle",
                "score": 0.8,
                "risk_level": "warning",
            }
        ],
    }
    gt = {"dangerous_objects": [{"label_name": "human"}]}
    reasons = identify_failures(
        current, {"track_distance_jump_m": 6.0}, gt=gt, previous_result=previous
    )
    assert "tracking_inconsistent" in reasons
    assert "missed_dangerous_object" in reasons
