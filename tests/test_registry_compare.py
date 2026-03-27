from lidar_perception.evaluation.model_comparison import compare_models


def test_compare_models_promote_when_safer():
    production = {
        "recall": 0.7,
        "dangerous_fnr": 0.3,
        "distance_mae": 4.0,
        "latency_ms": 10.0,
        "recall_human": 0.7,
        "recall_animal": 0.68,
        "recall_rock": 0.72,
        "recall_post": 0.65,
    }
    candidate = {
        "recall": 0.75,
        "dangerous_fnr": 0.25,
        "distance_mae": 3.5,
        "latency_ms": 11.0,
        "recall_human": 0.74,
        "recall_animal": 0.72,
        "recall_rock": 0.75,
        "recall_post": 0.69,
    }
    report = compare_models(production, candidate)
    assert report["promote"] is True


def test_compare_models_blocks_when_dangerous_class_recall_drops():
    production = {
        "recall": 0.70,
        "dangerous_fnr": 0.30,
        "distance_mae": 4.0,
        "latency_ms": 10.0,
        "recall_human": 0.78,
        "recall_animal": 0.71,
    }
    candidate = {
        "recall": 0.74,
        "dangerous_fnr": 0.27,
        "distance_mae": 3.8,
        "latency_ms": 11.0,
        "recall_human": 0.73,
        "recall_animal": 0.74,
    }
    report = compare_models(
        production,
        candidate,
        cfg={"min_dangerous_class_recall_gain": 0.0, "dangerous_classes": ["human", "animal"]},
    )
    assert report["promote"] is False
