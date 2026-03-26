from __future__ import annotations

import argparse

from torch.utils.data import DataLoader
import torch

from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.models.factory import build_model
from lidar_perception.training.engine import Trainer, maybe_load_weights
from lidar_perception.utils.config import load_config
from lidar_perception.utils.logging import setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LiDAR perception model")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    device = torch.device("cuda" if config.get("device") == "cuda" and torch.cuda.is_available() else "cpu")
    logger = setup_logger(config["output_dir"])

    dataset = build_dataset(config["data"], split="test")
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


if __name__ == "__main__":
    main()
