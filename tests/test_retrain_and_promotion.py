import json
from pathlib import Path

import yaml

from scripts import retrain as retrain_script
from scripts import promote_model


def test_retrain_writes_metadata_and_candidate_dir(tmp_path: Path, monkeypatch):
    cfg = {
        "seed": 1,
        "device": "cpu",
        "output_dir": str(tmp_path / "outputs"),
        "data": {
            "dataset_type": "synthetic_agriculture",
            "train_size": 2,
            "val_size": 1,
            "test_size": 1,
            "num_workers": 0,
            "batch_size": 1,
            "num_points": 200,
            "class_names": ["human", "animal", "vehicle", "post", "rock"],
            "dangerous_classes": ["human", "animal", "rock", "post"],
            "segmentation_classes": [
                "background",
                "traversable_ground",
                "vegetation",
                "vehicle",
                "human",
                "obstacle",
            ],
            "point_cloud_range": [-10, -10, -3, 10, 10, 3],
            "grid_size": [32, 32],
            "max_objects": 2,
            "augmentations": {"enabled": False},
            "simulation": {"terrain_variation": 0.0, "vegetation_density": 0.0},
            "preprocessing": {"enabled": False},
        },
        "model": {
            "name": "pointpillars_bev",
            "in_channels": 6,
            "base_channels": 8,
            "num_classes": 5,
            "num_segmentation_classes": 6,
            "score_threshold": 0.2,
            "nms_iou_threshold": 0.2,
            "max_detections": 8,
            "max_candidates_per_class": 8,
        },
        "training": {
            "epochs": 1,
            "learning_rate": 0.001,
            "weight_decay": 0.0,
            "mixed_precision": False,
            "losses": {"detection": 1.0, "segmentation": 1.0, "obstacle": 0.5},
        },
        "evaluation": {
            "iou_threshold": 0.25,
            "dangerous_iou_threshold": 0.2,
            "latency_warmup": 1,
            "latency_iters": 1,
        },
        "retrain": {
            "hard_case_ratio": 0.3,
            "oversample_dangerous_classes": True,
            "dangerous_class_weight": 2.0,
            "candidate_tag": "it",
        },
    }
    cfg_path = tmp_path / "retrain.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    monkeypatch.setattr(
        retrain_script,
        "parse_args",
        lambda: type("Args", (), {"config": str(cfg_path), "resume": None})(),
    )
    monkeypatch.setattr(retrain_script.Trainer, "fit", lambda self, train_loader, val_loader: None)

    retrain_script.main()

    meta = json.loads(Path("outputs/reports/retrain_metadata.json").read_text(encoding="utf-8"))
    assert "candidate_output_dir" in meta
    assert Path(meta["candidate_output_dir"]).exists()
    assert meta["hard_case_ratio"] == 0.3


def test_promote_model_archives_previous_and_promotes_candidate(tmp_path: Path, monkeypatch):
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir(parents=True)
    registry_path = registry_dir / "registry.json"
    registry_path.write_text(
        json.dumps(
            [
                {
                    "version": "v1",
                    "timestamp": "2026-01-01T00:00:00+00:00",
                    "status": "production",
                    "checkpoint": "prod.pt",
                    "config_hash": "",
                    "dataset_manifest": "",
                    "metrics": {},
                    "notes": "",
                },
                {
                    "version": "v2",
                    "timestamp": "2026-01-02T00:00:00+00:00",
                    "status": "candidate",
                    "checkpoint": "cand.pt",
                    "config_hash": "",
                    "dataset_manifest": "",
                    "metrics": {},
                    "notes": "",
                },
            ]
        ),
        encoding="utf-8",
    )
    report = tmp_path / "comparison.json"
    report.write_text(
        json.dumps({"promote": True, "decision_reason": "ok", "candidate": {}}), encoding="utf-8"
    )

    monkeypatch.setattr(
        promote_model,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "candidate_model": "cand.pt",
                "production_model": "prod.pt",
                "comparison_report": str(report),
                "registry_dir": str(registry_dir),
                "candidate_version": None,
                "production_version": None,
            },
        )(),
    )

    promote_model.main()
    entries = json.loads(registry_path.read_text(encoding="utf-8"))
    assert any(e["checkpoint"] == "cand.pt" and e["status"] == "production" for e in entries)
    assert any(e["checkpoint"] == "prod.pt" and e["status"] == "archived" for e in entries)
