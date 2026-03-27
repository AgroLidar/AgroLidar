from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader
from tqdm import tqdm

from lidar_perception.evaluation.robustness import measure_latency, perturb_bev, robustness_gap
from lidar_perception.inference.predictor import Predictor
from lidar_perception.training.losses import detection_loss, obstacle_loss, segmentation_loss
from lidar_perception.training.metrics import (
    compute_dangerous_fnr,
    compute_detection_map,
    compute_obstacle_distance_error,
    compute_per_class_detection_metrics,
    compute_segmentation_iou,
)
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
        self.scaler = GradScaler(enabled=bool(config["training"].get("mixed_precision", False)) and device.type == "cuda")
        self.predictor = Predictor(model, config, device)
        self.best_score = float("-inf")
        self.start_epoch = 1

    def resume_if_available(self, checkpoint_path: str | None) -> None:
        if not checkpoint_path:
            return
        payload = load_checkpoint(checkpoint_path, self.model, self.optimizer, self.device)
        if isinstance(payload, dict):
            self.start_epoch = int(payload.get("epoch", 0)) + 1
            metrics = payload.get("metrics", {})
            self.best_score = float(metrics.get("mAP", float("-inf")))
            self.logger.info("resumed checkpoint=%s from epoch=%s", checkpoint_path, self.start_epoch)

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
            if self.config["training"].get("grad_clip_norm") is not None:
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

                if "segmentation_target" in batch:
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

                if "boxes" in batch:
                    for idx in range(bev.shape[0]):
                        single_outputs = {
                            "detection": {k: v[idx : idx + 1] for k, v in outputs["detection"].items()},
                        }
                        predictions.append(self.predictor.decode_detections(single_outputs))
                        targets.append({"boxes": batch["boxes"][idx], "labels": batch["labels"][idx]})

        dangerous_names = set(self.config["data"].get("dangerous_classes", []))
        dangerous_labels = {idx for idx, name in enumerate(self.config["data"]["class_names"]) if name in dangerous_names}
        if predictions and targets:
            map_metrics = compute_detection_map(predictions, targets, self.config["evaluation"]["iou_threshold"])
            dangerous_metrics = compute_dangerous_fnr(
                predictions,
                targets,
                dangerous_labels,
                self.config["evaluation"]["dangerous_iou_threshold"],
            )
            per_class_metrics = compute_per_class_detection_metrics(
                predictions,
                targets,
                self.config["data"]["class_names"],
                self.config["evaluation"]["iou_threshold"],
            )
        else:
            map_metrics = {"mAP": 0.0, "precision": 0.0, "recall": 0.0}
            dangerous_metrics = {"dangerous_fnr": 1.0}
            per_class_metrics = {
                cls: {"precision": 0.0, "recall": 0.0, "false_negative_rate": 1.0, "distance_error": float("inf")}
                for cls in self.config["data"]["class_names"]
            }

        latency_metrics = measure_latency(
            self.model,
            next(iter(loader))["bev"][:1],
            self.device,
            self.config["evaluation"]["latency_warmup"],
            self.config["evaluation"]["latency_iters"],
        )
        clean_seg = float(sum(seg_iou) / max(len(seg_iou), 1))
        degraded_seg = float(sum(degraded_seg_iou) / max(len(degraded_seg_iou), 1)) if degraded_seg_iou else clean_seg
        metrics = {
            "mAP": map_metrics["mAP"],
            "precision": map_metrics["precision"],
            "recall": map_metrics["recall"],
            "segmentation_iou": clean_seg,
            "distance_mae": float(sum(distance_errors) / max(len(distance_errors), 1)) if distance_errors else float("inf"),
            "dangerous_fnr": dangerous_metrics["dangerous_fnr"],
            "avg_batch_latency_ms": float((total_inference_time * 1000.0) / max(num_batches, 1)),
            "latency_ms": latency_metrics["latency_ms"],
            "fps": latency_metrics["fps"],
            "robustness_gap": robustness_gap(clean_seg, degraded_seg)["robustness_gap"],
        }
        dangerous_scores = []
        for class_name, cls_metrics in per_class_metrics.items():
            metrics[f"recall_{class_name}"] = float(cls_metrics["recall"])
            metrics[f"fnr_{class_name}"] = float(cls_metrics["false_negative_rate"])
            metrics[f"precision_{class_name}"] = float(cls_metrics["precision"])
            metrics[f"distance_error_{class_name}"] = float(cls_metrics["distance_error"])
            if class_name in dangerous_names:
                dangerous_scores.append((cls_metrics["recall"] + (1.0 - cls_metrics["false_negative_rate"])) / 2.0)
        metrics["dangerous_class_aggregate_score"] = float(sum(dangerous_scores) / max(len(dangerous_scores), 1))
        return metrics

    def fit(self, train_loader: DataLoader, val_loader: DataLoader, epoch_end_callback=None) -> None:
        checkpoint_dir = Path(self.config["output_dir"]) / "checkpoints"
        metrics_dir = Path(self.config["output_dir"]) / "metrics"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metrics_log = metrics_dir / "train_metrics.jsonl"
        early = self.config["training"].get("early_stopping", {})
        early_enabled = bool(early.get("enabled", False))
        patience = int(early.get("patience", 5))
        min_delta = float(early.get("min_delta", 0.0))
        stale_epochs = 0

        for epoch in range(self.start_epoch, self.config["training"]["epochs"] + 1):
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
            record = {"epoch": epoch, "train": train_metrics, "val": val_metrics}
            with metrics_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            if epoch_end_callback is not None:
                try:
                    current_lr = float(self.optimizer.param_groups[0]["lr"])
                    epoch_end_callback(epoch=epoch, train_metrics=train_metrics, val_metrics=val_metrics, lr=current_lr)
                except Exception:
                    self.logger.exception("epoch_end_callback failed at epoch=%s", epoch)

            score = val_metrics["mAP"] + val_metrics["segmentation_iou"] + val_metrics["recall"] - val_metrics["dangerous_fnr"]
            checkpoint_metrics = dict(val_metrics)
            checkpoint_metrics["val_loss"] = float(max(0.0, 1.0 - val_metrics["mAP"]))
            latest_path = checkpoint_dir / "latest.pt"
            save_checkpoint(latest_path, self.model, self.optimizer, epoch, checkpoint_metrics, self.config)
            if score > (self.best_score + min_delta):
                self.best_score = score
                stale_epochs = 0
                save_checkpoint(checkpoint_dir / "best.pt", self.model, self.optimizer, epoch, checkpoint_metrics, self.config)
            else:
                stale_epochs += 1
                if early_enabled and stale_epochs >= patience:
                    self.logger.info("early_stopping triggered at epoch=%s", epoch)
                    break


def maybe_load_weights(model: torch.nn.Module, optimizer: torch.optim.Optimizer, checkpoint_path: str | None, device: torch.device):
    if checkpoint_path:
        return load_checkpoint(checkpoint_path, model, optimizer, device)
    return None
