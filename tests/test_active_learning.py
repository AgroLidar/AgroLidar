from lidar_perception.active_learning.miner import score_candidate


def test_score_candidate_flags_dangerous():
    result = {
        "detections": [
            {"label_name": "human", "score": 0.21, "distance_m": 46.0, "risk_level": "warning"},
            {"label_name": "post", "score": 0.45, "distance_m": 12.0, "risk_level": "monitor"},
        ]
    }
    cfg = {"min_score_threshold": 0.3}
    c = score_candidate("s1", result, cfg)
    assert c.score > 0.0
    assert "dangerous_ambiguous" in c.reasons
