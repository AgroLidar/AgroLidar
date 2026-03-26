from __future__ import annotations

from pathlib import Path
import time

import torch
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader
from tqdm import tqdm

from lidar_perception.evaluation.robustness import measure_latency, perturb_bev, robustness_gap
from lidar_perception.inference.predictor import Predictor
from lidar_perception.training.losses import detection_loss, obstacle_loss, segmentation_loss
from lidar_perception.training.metrics import compute_dangerous_fnr, compute_detection_map, compute_obstacle_distance_error, compute_segmentation_iou
from lidar_perception.utils.checkpoint import load_checkpoint, save_checkpoint


class Trainer:
    def __init__(self, model: torch.nn.Module, config: dict, logger, device: torch.device):
        self.model = model
        self.config = config
        self.logger = logger
        self.device = device
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=float(config["training"]["learning_rate"]),
            weight_decay=float(config["training"]["weight_decay"]),
        )
        self.scaler = GradScaler(enabled=bool(config["training"]["mixed_precision"]) and device.type == "cuda")
        self.predictor = Predictor(model, config, device)
        self.best_score = float("-inf")

    def _move_targets(self, batch: dict) -> tuple[dict, torch.Tensor, dict]:
        detection_target = {k: v.to(self.device) for k, v in batch["detection_target"].items()}
        segmentation_target = batch["segmentation_target"].to(self.device)
        obstacle_target = {k: v.to(self.device) for k, v in batch["obstacle_target"].items()}
        return detection_target, segmentation_target, obstacle_target

    def train_epoch(self, loader: DataLoader, epoch: int) -> dict[str, float]:
        self.model.train()
        running = {"loss": 0.0}
        progress = tqdm(loader, desc=f"train {epoch}", leave=False)

        for step, batch in enumerate(progress, start=1):
            bev = batch["bev"].to(self.device)
            detection_target, segmentation_target, obstacle_target = self._move_targets(batch)
            self.optimizer.zero_grad(set_to_none=True)

            with autocast(enabled=self.scaler.is_enabled()):
                outputs = self.model(bev)
                det_loss = detection_loss(outputs["detection"], detection_target)
                seg_loss = segmentation_loss(outputs["segmentation"], segmentation_target)
                obs_loss = obstacle_loss(outputs["obstacle"], obstacle_target)
                loss = (
                    self.config["training"]["losses"]["detection"] * det_loss
                    + self.config["training"]["losses"]["segmentation"] * seg_loss
                    + self.config["training"]["losses"]["obstacle"] * obs_loss
                )

            self.scaler.scale(loss).backward()
            if self.config["training"]["grad_clip_norm"] is not None:
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config["training"]["grad_clip_norm"])
            self.scaler.step(self.optimizer)
            self.scaler.update()

            running["loss"] += loss.item()
            progress.set_postfix(loss=f"{running['loss'] / step:.4f}")

        running["loss"] /= max(len(loader), 1)
        return running

    def evaluate(self, loader: DataLoader) -> dict[str, float]:
        self.model.eval()
        predictions = []
        targets = []
        seg_iou = []
        distance_errors = []
        degraded_seg_iou = []
        total_inference_time = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in tqdm(loader, desc="eval", leave=False):
                bev = batch["bev"].to(self.device)
                start = time.perf_counter()
                outputs = self.model(bev)
                total_inference_time += time.perf_counter() - start
                num_batches += 1

                seg_iou.append(
                    compute_segmentation_iou(
                        outputs["segmentation"].cpu(),
                        batch["segmentation_target"],
                        self.config["model"]["num_segmentation_classes"],
                    )["iou"]
                )
                obstacle_metrics = compute_obstacle_distance_error(
                    torch.sigmoid(outputs["obstacle"]["distance"]).cpu(),
                    batch["obstacle_target"]["distance"],
                    batch["obstacle_target"]["occupancy"],
                )
                distance_errors.append(obstacle_metrics["distance_mae"])
                degraded_outputs = self.model(perturb_bev(bev, severity=0.2))
                degraded_seg_iou.append(
                    compute_segmentation_iou(
                        degraded_outputs["segmentation"].cpu(),
                        batch["segmentation_target"],
                        self.config["model"]["num_segmentation_classes"],
                    )["iou"]
                )

                for idx in range(bev.shape[0]):
                    single_outputs = {
                        "detection": {k: v[idx : idx + 1] for k, v in outputs["detection"].items()},
                    }
                    predictions.append(self.predictor.decode_detections(single_outputs))
                    targets.append({"boxes": batch["boxes"][idx], "labels": batch["labels"][idx]})

        map_metrics = compute_detection_map(predictions, targets, self.config["evaluation"]["iou_threshold"])
        dangerous_names = set(self.config["data"].get("dangerous_classes", []))
        dangerous_labels = {idx for idx, name in enumerate(self.config["data"]["class_names"]) if name in dangerous_names}
        dangerous_metrics = compute_dangerous_fnr(
            predictions,
            targets,
            dangerous_labels,
            self.config["evaluation"]["dangerous_iou_threshold"],
        )
        latency_metrics = measure_latency(
            self.model,
            next(iter(loader))["bev"][:1],
            self.device,
            self.config["evaluation"]["latency_warmup"],
            self.config["evaluation"]["latency_iters"],
        )
        clean_seg = float(sum(seg_iou) / max(len(seg_iou), 1))
        degraded_seg = float(sum(degraded_seg_iou) / max(len(degraded_seg_iou), 1))
        metrics = {
            "mAP": map_metrics["mAP"],
            "precision": map_metrics["precision"],
            "recall": map_metrics["recall"],
            "segmentation_iou": clean_seg,
            "distance_mae": float(sum(distance_errors) / max(len(distance_errors), 1)),
            "dangerous_fnr": dangerous_metrics["dangerous_fnr"],
            "avg_batch_latency_ms": float((total_inference_time * 1000.0) / max(num_batches, 1)),
            "latency_ms": latency_metrics["latency_ms"],
            "fps": latency_metrics["fps"],
            "robustness_gap": robustness_gap(clean_seg, degraded_seg)["robustness_gap"],
        }
        return metrics

    def fit(self, train_loader: DataLoader, val_loader: DataLoader) -> None:
        checkpoint_dir = Path(self.config["output_dir"]) / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        for epoch in range(1, self.config["training"]["epochs"] + 1):
            train_metrics = self.train_epoch(train_loader, epoch)
            val_metrics = self.evaluate(val_loader)
            self.logger.info(
                "epoch=%s train_loss=%.4f val_mAP=%.4f val_iou=%.4f val_recall=%.4f val_fnr=%.4f val_distance_mae=%.4f",
                epoch,
                train_metrics["loss"],
                val_metrics["mAP"],
                val_metrics["segmentation_iou"],
                val_metrics["recall"],
                val_metrics["dangerous_fnr"],
                val_metrics["distance_mae"],
            )
            score = val_metrics["mAP"] + val_metrics["segmentation_iou"] + val_metrics["recall"] - val_metrics["dangerous_fnr"]
            latest_path = checkpoint_dir / "latest.pt"
            save_checkpoint(latest_path, self.model, self.optimizer, epoch, val_metrics, self.config)
            if score > self.best_score:
                self.best_score = score
                save_checkpoint(checkpoint_dir / "best.pt", self.model, self.optimizer, epoch, val_metrics, self.config)


def maybe_load_weights(model: torch.nn.Module, optimizer: torch.optim.Optimizer, checkpoint_path: str | None, device: torch.device):
    if checkpoint_path:
        return load_checkpoint(checkpoint_path, model, optimizer, device)
    return None
