from lidar_perception.evaluation.model_comparison import compare_models


def test_compare_models_promote_when_safer():
    production = {"recall": 0.7, "dangerous_fnr": 0.3, "distance_mae": 4.0, "latency_ms": 10.0}
    candidate = {"recall": 0.75, "dangerous_fnr": 0.25, "distance_mae": 3.5, "latency_ms": 11.0}
    report = compare_models(production, candidate)
    assert report["promote"] is True
