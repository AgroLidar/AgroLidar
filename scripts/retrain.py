from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import copy
import json
import random

import numpy as np
import torch
from torch.utils.data import DataLoader

from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.data.hard_case_dataset import (
    CompositeTrainingDataset,
    ReviewedHardCaseDataset,
)
from lidar_perception.models.factory import build_model
from lidar_perception.training.engine import Trainer
from lidar_perception.utils.config import load_config
from lidar_perception.utils.logging import setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline retraining with reviewed hard cases")
    parser.add_argument("--config", default="configs/retrain.yaml")
    parser.add_argument("--resume", default=None)
    return parser.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve_device(device_name: str) -> torch.device:
    if device_name == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def class_distribution(dataset, class_names: list[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for i in range(len(dataset)):
        sample = dataset[i]
        labels = sample.get("labels")
        if labels is None:
            continue
        label_values = labels.tolist() if hasattr(labels, "tolist") else list(labels)
        for label in label_values:
            idx = int(label)
            if 0 <= idx < len(class_names):
                counts[class_names[idx]] += 1
    return {name: int(counts.get(name, 0)) for name in class_names}


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    seed_everything(int(config["seed"]))

    retrain_cfg = config.get("retrain", {})
    data_cfg = copy.deepcopy(config["data"])

    hard_case_ratio = float(retrain_cfg.get("hard_case_ratio", 0.3))
    oversample_dangerous = bool(retrain_cfg.get("oversample_dangerous_classes", True))
    dangerous_class_weight = float(retrain_cfg.get("dangerous_class_weight", 2.0))
    candidate_tag = retrain_cfg.get("candidate_tag", "retrain_candidate")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_output = Path(config.get("output_dir", "outputs"))
    candidate_output = base_output / "candidates" / f"{candidate_tag}_{ts}"

    run_config = copy.deepcopy(config)
    run_config["output_dir"] = str(candidate_output)
    run_config["training"]["epochs"] = int(retrain_cfg.get("epochs", 1))

    # Keep retraining iterations bounded by default so frequent offline cycles stay practical.
    data_cfg["train_size"] = int(
        min(data_cfg.get("train_size", 0) or 0, retrain_cfg.get("base_train_size_cap", 120))
        or retrain_cfg.get("base_train_size_cap", 120)
    )
    data_cfg["val_size"] = int(
        min(data_cfg.get("val_size", 0) or 0, retrain_cfg.get("base_val_size_cap", 40))
        or retrain_cfg.get("base_val_size_cap", 40)
    )

    candidate_output.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(str(candidate_output))
    device = resolve_device(run_config.get("device", "cpu"))
    logger.info("using device=%s", device)

    base_train_dataset = build_dataset(data_cfg, split="train")
    data_cfg["hard_case"] = {
        "dirs": retrain_cfg.get("hard_case_dirs", ["data/hard_cases", "data/review_queue"]),
        "manifests": retrain_cfg.get("hard_case_manifests", []),
        "only_reviewed": bool(retrain_cfg.get("reviewed_only", True)),
        "only_high_conf_failures": bool(retrain_cfg.get("only_high_conf_failures", False)),
        "min_failure_confidence": float(retrain_cfg.get("min_failure_confidence", 0.5)),
    }
    hard_dataset = ReviewedHardCaseDataset(data_cfg, split="train")

    dangerous_label_ids = [
        idx
        for idx, name in enumerate(data_cfg.get("class_names", []))
        if name in set(data_cfg.get("dangerous_classes", []))
    ]
    train_dataset = CompositeTrainingDataset(
        base_train_dataset,
        hard_dataset,
        hard_case_ratio=hard_case_ratio,
        oversample_dangerous_classes=oversample_dangerous,
        dangerous_classes=dangerous_label_ids,
        dangerous_class_weight=dangerous_class_weight,
        hazard_weighting=True,
        uncertainty_weighting=True,
        seed=int(run_config["seed"]),
    )
    val_dataset = build_dataset(data_cfg, split="val")

    train_loader = DataLoader(
        train_dataset,
        batch_size=data_cfg["batch_size"],
        shuffle=True,
        num_workers=data_cfg["num_workers"],
        collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=data_cfg["batch_size"],
        shuffle=False,
        num_workers=data_cfg["num_workers"],
        collate_fn=collate_fn,
    )

    model = build_model(run_config["model"]).to(device)
    trainer = Trainer(model=model, config=run_config, logger=logger, device=device)
    trainer.resume_if_available(args.resume)

    hard_distribution = class_distribution(hard_dataset, data_cfg["class_names"])
    composition = train_dataset.composition()
    logger.info("hard_cases_used=%s", len(hard_dataset))
    logger.info("hard_case_class_distribution=%s", hard_distribution)
    logger.info("dataset_composition=%s", composition)

    meta = {
        "base_config": args.config,
        "candidate_output_dir": str(candidate_output),
        "hard_cases_used": len(hard_dataset),
        "hard_case_ratio": hard_case_ratio,
        "oversample_dangerous_classes": oversample_dangerous,
        "dangerous_class_weight": dangerous_class_weight,
        "hard_case_class_distribution": hard_distribution,
        "dataset_composition": composition,
    }
    meta_path = Path("outputs/reports/retrain_metadata.json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    trainer.fit(train_loader, val_loader)


if __name__ == "__main__":
    main()
