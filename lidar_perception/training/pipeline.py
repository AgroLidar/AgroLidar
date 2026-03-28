"""Training pipeline service layer used by CLI adapters."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from lidar_perception.config import TrainConfig
from lidar_perception.data.datasets import build_dataset, collate_fn
from lidar_perception.logging_config import configure_logging
from lidar_perception.models.factory import build_model
from lidar_perception.tracking import MLflowTracker, flatten_dict
from lidar_perception.training.engine import Trainer
from lidar_perception.utils.config import load_config

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Outcome object for training pipeline execution."""

    success: bool


class TrainingPipeline:
    """Application service that orchestrates end-to-end model training."""

    def __init__(self, config: TrainConfig):
        """Initialize training pipeline.

        Args:
            config: Validated training configuration.
        """
        self.config = config

    @staticmethod
    def _seed_everything(seed: int) -> None:
        """Seed random generators for reproducibility.

        Args:
            seed: Integer random seed.
        """
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    @staticmethod
    def _resolve_device(device_name: str) -> torch.device:
        """Resolve a torch device from requested name.

        Args:
            device_name: Desired device string.

        Returns:
            Selected torch device.
        """
        if device_name == "cuda" and torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def run(self) -> TrainingResult:
        """Execute model training lifecycle.

        Returns:
            Structured training result with success flag.
        """
        configure_logging()
        raw_cfg_path = self.config.config_path or Path("configs/train.yaml")
        raw_config = load_config(str(raw_cfg_path))
        tracker = MLflowTracker("configs/mlflow.yaml")
        run_name = f"train_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        self._seed_everything(self.config.seed)
        Path(raw_config["output_dir"]).mkdir(parents=True, exist_ok=True)
        device = self._resolve_device(raw_config.get("device", self.config.device))
        logger.info("using device=%s", device)

        train_dataset = build_dataset(raw_config["data"], split="train")
        val_dataset = build_dataset(raw_config["data"], split="val")
        train_loader = DataLoader(
            train_dataset,
            batch_size=raw_config["data"]["batch_size"],
            shuffle=True,
            num_workers=raw_config["data"]["num_workers"],
            collate_fn=collate_fn,
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=raw_config["data"]["batch_size"],
            shuffle=False,
            num_workers=raw_config["data"]["num_workers"],
            collate_fn=collate_fn,
        )

        model = build_model(raw_config["model"]).to(device)
        trainer = Trainer(model=model, config=raw_config, logger=logger, device=device)
        best_epoch: dict[str, int | None] = {"value": None}
        best_val_loss = float("inf")

        with tracker.start_run(run_name=run_name, tags={"run_type": "training"}):
            tracker.log_params(flatten_dict(raw_config))
            tracker.log_config(str(raw_cfg_path))
            tracker.log_model_summary(model)

            def _on_epoch_end(
                epoch: int, train_metrics: dict, val_metrics: dict, lr: float
            ) -> None:
                nonlocal best_val_loss
                train_loss = float(train_metrics.get("loss", 0.0))
                val_loss = float(max(0.0, 1.0 - float(val_metrics.get("mAP", 0.0))))
                tracker.log_metric("train_loss", train_loss, step=epoch)
                tracker.log_metric("val_loss", val_loss, step=epoch)
                tracker.log_metric("lr", lr, step=epoch)
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_epoch["value"] = epoch

            try:
                trainer.fit(train_loader, val_loader, epoch_end_callback=_on_epoch_end)
                best_checkpoint = Path(raw_config["output_dir"]) / "checkpoints" / "best.pt"
                tracker.log_checkpoint(best_checkpoint, name="checkpoint")
                if best_epoch["value"] is not None:
                    tracker.set_tag("best_epoch", best_epoch["value"])
                tracker.set_tag("training_status", "completed")
                tracker.end_run("FINISHED")
                return TrainingResult(success=True)
            except Exception:
                tracker.set_tag("training_status", "failed")
                tracker.end_run("FAILED")
                logger.exception("Training pipeline failed")
                return TrainingResult(success=False)
