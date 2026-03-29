from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import torch
from torch.utils.data import DataLoader

from lidar_perception.config import EvalConfig
from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.models.factory import build_model
from lidar_perception.tracking import MLflowTracker, flatten_dict
from lidar_perception.training.engine import Trainer, maybe_load_weights
from lidar_perception.utils.logging import setup_logger

SAFETY_CLASSES = ["human", "animal", "rock", "post", "vehicle"]
MetricsMap = dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LiDAR perception model")
    parser.add_argument("--config", default="configs/eval.yaml")
    parser.add_argument("--checkpoint", required=False, default=None)
    parser.add_argument("--split", default=None)
    return parser.parse_args()


def _resolve_checkpoint(config: EvalConfig, checkpoint_arg: str | None) -> str:
    if checkpoint_arg:
        return checkpoint_arg
    if config.checkpoint_path is not None and config.checkpoint_path.exists():
        return str(config.checkpoint_path)

    output_dir = Path(config.output_dir)
    for candidate in [output_dir / "checkpoints" / "best.pt", output_dir / "checkpoints" / "latest.pt"]:
        if candidate.exists():
            return str(candidate)

    candidate_runs = sorted(
        (output_dir / "candidates").glob("*/checkpoints/best.pt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidate_runs:
        return str(candidate_runs[0])

    raise FileNotFoundError(
        "No checkpoint provided and no default checkpoint found under outputs/checkpoints or outputs/candidates"
    )


def _metric_as_float(metrics: Mapping[str, Any], key: str, default: float) -> float:
    value = metrics.get(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    return default


def render_markdown(metrics: Mapping[str, Any]) -> str:
    lines = [
        "# AgroLidar Evaluation Report",
        "",
        "## Core Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in [
        "mAP",
        "precision",
        "recall",
        "dangerous_fnr",
        "dangerous_class_aggregate_score",
        "segmentation_iou",
        "distance_mae",
        "latency_ms",
        "fps",
        "robustness_gap",
    ]:
        if key in metrics:
            value = metrics[key]
            lines.append(
                f"| {key} | {value:.6f} |" if isinstance(value, float) else f"| {key} | {value} |"
            )

    lines += [
        "",
        "## Safety-Critical Per-Class Metrics",
        "",
        "| Class | Recall | FNR | Precision | Distance Error |",
        "|---|---:|---:|---:|---:|",
    ]
    for cls in SAFETY_CLASSES:
        rec = _metric_as_float(metrics, f"recall_{cls}", 0.0)
        fnr = _metric_as_float(metrics, f"fnr_{cls}", 1.0)
        prec = _metric_as_float(metrics, f"precision_{cls}", 0.0)
        dist = _metric_as_float(metrics, f"distance_error_{cls}", float("inf"))
        lines.append(f"| {cls} | {rec:.6f} | {fnr:.6f} | {prec:.6f} | {dist:.6f} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    config = EvalConfig.from_yaml(args.config)
    tracker = MLflowTracker("configs/mlflow.yaml")
    run_name = f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    training_cfg = dict(config.training)
    training_cfg.setdefault("learning_rate", 1e-3)
    training_cfg.setdefault("weight_decay", 0.0)
    training_cfg.setdefault("mixed_precision", False)

    split = args.split or str(config.evaluation.get("split", "test"))
    checkpoint = _resolve_checkpoint(config, args.checkpoint)
    device = torch.device("cuda" if config.device == "cuda" and torch.cuda.is_available() else "cpu")
    logger = setup_logger(str(config.output_dir))

    dataset = build_dataset(config.data, split=split)
    loader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=int(config.data.get("num_workers", 0)),
        collate_fn=collate_fn,
    )

    runtime_config = config.model_dump(mode="python")
    runtime_config["training"] = training_cfg
    model = build_model(config.model).to(device)
    trainer = Trainer(model=model, config=runtime_config, logger=logger, device=device)
    maybe_load_weights(model, trainer.optimizer, checkpoint, device)
    metrics: MetricsMap = trainer.evaluate(loader)

    per_class: dict[str, dict[str, float]] = {}
    class_names = config.data.get("class_names", SAFETY_CLASSES)
    for cls in class_names:
        per_class[str(cls)] = {
            "recall": _metric_as_float(metrics, f"recall_{cls}", 0.0),
            "precision": _metric_as_float(metrics, f"precision_{cls}", 0.0),
            "fnr": _metric_as_float(metrics, f"fnr_{cls}", 1.0),
            "distance_error": _metric_as_float(metrics, f"distance_error_{cls}", float("inf")),
        }
    metrics["per_class"] = per_class
    metrics["latency"] = _metric_as_float(
        metrics,
        "latency_ms",
        _metric_as_float(metrics, "avg_batch_latency_ms", 0.0),
    )
    logger.info("evaluation metrics: %s", metrics)

    json_path = Path(str(config.evaluation.get("save_json", "outputs/reports/eval_report.json")))
    md_path = Path(str(config.evaluation.get("save_md", "outputs/reports/eval_report.md")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(metrics), encoding="utf-8")

    with tracker.start_run(run_name=run_name, tags={"run_type": "evaluation"}):
        latest_train_run = tracker.latest_run_id(run_type="training")
        if latest_train_run:
            tracker.set_tag("train_run_id", latest_train_run)
        tracker.log_params(flatten_dict(runtime_config))
        eval_metrics = {f"eval/{k}": float(v) for k, v in metrics.items() if isinstance(v, (int, float))}
        tracker.log_metrics(eval_metrics)
        if "dangerous_fnr" in metrics:
            tracker.log_metric("eval/dangerous_fnr", _metric_as_float(metrics, "dangerous_fnr", 0.0))
        tracker.log_eval_report(json_path)
        tracker.log_eval_report(md_path)
        model_tag = str(config.evaluation.get("model_tag", "candidate"))
        tracker.set_tag("model_tag", model_tag)
        tracker.end_run("FINISHED")

    logger.info(
        "evaluation reports written",
        extra={"json": str(json_path), "markdown": str(md_path), "checkpoint": checkpoint},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
