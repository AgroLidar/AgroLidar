"""Entrypoint de entrenamiento end-to-end.

Carga configuración YAML, construye datasets/dataloaders para train/val, inicializa
el modelo y ejecuta el loop de entrenamiento con `Trainer.fit`, guardando checkpoints
en `outputs/checkpoints/`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.models.factory import build_model
from lidar_perception.training.engine import Trainer
from lidar_perception.utils.config import load_config
from lidar_perception.utils.logging import setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train LiDAR perception model")
    parser.add_argument("--config", default="configs/train.yaml", help="Path to YAML config")
    parser.add_argument("--resume", default=None, help="Optional checkpoint to resume from")
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


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    seed_everything(int(config["seed"]))
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)
    logger = setup_logger(config["output_dir"])
    device = resolve_device(config.get("device", "cpu"))
    logger.info("using device=%s", device)

    train_dataset = build_dataset(config["data"], split="train")
    val_dataset = build_dataset(config["data"], split="val")
    train_loader = DataLoader(
        train_dataset,
        batch_size=config["data"]["batch_size"],
        shuffle=True,
        num_workers=config["data"]["num_workers"],
        collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config["data"]["batch_size"],
        shuffle=False,
        num_workers=config["data"]["num_workers"],
        collate_fn=collate_fn,
    )

    model = build_model(config["model"]).to(device)
    trainer = Trainer(model=model, config=config, logger=logger, device=device)
    trainer.resume_if_available(args.resume)
    trainer.fit(train_loader, val_loader)


if __name__ == "__main__":
    main()
