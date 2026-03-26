from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from torch.utils.data import DataLoader
import torch

from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.models.factory import build_model
from lidar_perception.training.engine import Trainer, maybe_load_weights
from lidar_perception.utils.config import load_config
from lidar_perception.utils.logging import setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LiDAR perception model")
    parser.add_argument("--config", default="configs/eval.yaml")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--split", default=None)
    return parser.parse_args()


def render_markdown(metrics: dict) -> str:
    lines = ["# AgroLidar Evaluation Report", "", "| Metric | Value |", "|---|---:|"]
    for key, value in metrics.items():
        lines.append(f"| {key} | {value:.6f} |" if isinstance(value, float) else f"| {key} | {value} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    split = args.split or config.get("evaluation", {}).get("split", "test")
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
    maybe_load_weights(model, trainer.optimizer, args.checkpoint, device)
    metrics = trainer.evaluate(loader)
    logger.info("evaluation metrics: %s", metrics)

    json_path = Path(config.get("evaluation", {}).get("save_json", "outputs/reports/eval_report.json"))
    md_path = Path(config.get("evaluation", {}).get("save_md", "outputs/reports/eval_report.md"))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(metrics), encoding="utf-8")


if __name__ == "__main__":
    main()
