from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json

from torch.utils.data import DataLoader
import torch

from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.models.factory import build_model
from lidar_perception.training.engine import Trainer, maybe_load_weights
from lidar_perception.utils.config import load_config
from lidar_perception.utils.logging import setup_logger


SAFETY_CLASSES = ["human", "animal", "rock", "post", "vehicle"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LiDAR perception model")
    parser.add_argument("--config", default="configs/eval.yaml")
    parser.add_argument("--checkpoint", required=False, default=None)
    parser.add_argument("--split", default=None)
    return parser.parse_args()


def _resolve_checkpoint(config: dict, checkpoint_arg: str | None) -> str:
    if checkpoint_arg:
        return checkpoint_arg
    output_dir = Path(config.get("output_dir", "outputs"))
    for candidate in [output_dir / "checkpoints" / "best.pt", output_dir / "checkpoints" / "latest.pt"]:
        if candidate.exists():
            return str(candidate)

    candidate_runs = sorted((output_dir / "candidates").glob("*/checkpoints/best.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidate_runs:
        return str(candidate_runs[0])

    raise FileNotFoundError("No checkpoint provided and no default checkpoint found under outputs/checkpoints or outputs/candidates")


def render_markdown(metrics: dict) -> str:
    lines = ["# AgroLidar Evaluation Report", "", "## Core Metrics", "", "| Metric | Value |", "|---|---:|"]
    for key in ["mAP", "precision", "recall", "dangerous_fnr", "dangerous_class_aggregate_score", "segmentation_iou", "distance_mae", "latency_ms", "fps", "robustness_gap"]:
        if key in metrics:
            value = metrics[key]
            lines.append(f"| {key} | {value:.6f} |" if isinstance(value, float) else f"| {key} | {value} |")

    lines += ["", "## Safety-Critical Per-Class Metrics", "", "| Class | Recall | FNR | Precision | Distance Error |", "|---|---:|---:|---:|---:|"]
    for cls in SAFETY_CLASSES:
        rec = metrics.get(f"recall_{cls}", 0.0)
        fnr = metrics.get(f"fnr_{cls}", 1.0)
        prec = metrics.get(f"precision_{cls}", 0.0)
        dist = metrics.get(f"distance_error_{cls}", float("inf"))
        lines.append(f"| {cls} | {rec:.6f} | {fnr:.6f} | {prec:.6f} | {dist:.6f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if "training" not in config:
        config["training"] = {"learning_rate": 1e-3, "weight_decay": 0.0, "mixed_precision": False}
    else:
        config["training"].setdefault("learning_rate", 1e-3)
        config["training"].setdefault("weight_decay", 0.0)
        config["training"].setdefault("mixed_precision", False)
    split = args.split or config.get("evaluation", {}).get("split", "test")
    checkpoint = _resolve_checkpoint(config, args.checkpoint)
    device = torch.device("cuda" if config.get("device") == "cuda" and torch.cuda.is_available() else "cpu")
    logger = setup_logger(config["output_dir"])

    dataset = build_dataset(config["data"], split=split)
    loader = DataLoader(
        dataset,
        batch_size=config["data"]["batch_size"],
        shuffle=False,
        num_workers=config["data"]["num_workers"],
        collate_fn=collate_fn,
    )

    model = build_model(config["model"]).to(device)
    trainer = Trainer(model=model, config=config, logger=logger, device=device)
    maybe_load_weights(model, trainer.optimizer, checkpoint, device)
    metrics = trainer.evaluate(loader)
    per_class = {}
    for cls in config["data"].get("class_names", SAFETY_CLASSES):
        per_class[cls] = {
            "recall": float(metrics.get(f"recall_{cls}", 0.0)),
            "precision": float(metrics.get(f"precision_{cls}", 0.0)),
            "fnr": float(metrics.get(f"fnr_{cls}", 1.0)),
            "distance_error": float(metrics.get(f"distance_error_{cls}", float("inf"))),
        }
    metrics["per_class"] = per_class
    metrics["latency"] = float(metrics.get("latency_ms", metrics.get("avg_batch_latency_ms", 0.0)))
    logger.info("evaluation metrics: %s", metrics)

    json_path = Path(config.get("evaluation", {}).get("save_json", "outputs/reports/eval_report.json"))
    md_path = Path(config.get("evaluation", {}).get("save_md", "outputs/reports/eval_report.md"))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(metrics), encoding="utf-8")

    print(f"evaluation_saved_json={json_path} evaluation_saved_md={md_path} checkpoint={checkpoint}")


if __name__ == "__main__":
    main()
