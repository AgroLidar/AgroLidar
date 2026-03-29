from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, TypeAlias

import numpy as np
import torch
from numpy.typing import NDArray

DetectionDict = dict[str, Any]
TargetDict = Mapping[str, torch.Tensor]
FloatArray: TypeAlias = NDArray[np.float32]


def compute_segmentation_iou(
    logits: torch.Tensor, target: torch.Tensor, num_classes: int
) -> dict[str, float]:
    pred = logits.argmax(dim=1)
    ious = []
    for cls in range(num_classes):
        pred_mask = pred == cls
        target_mask = target == cls
        intersection = (pred_mask & target_mask).sum().item()
        union = (pred_mask | target_mask).sum().item()
        if union > 0:
            ious.append(intersection / union)
    return {"iou": float(sum(ious) / max(len(ious), 1))}


def bev_iou(box_a: FloatArray, box_b: FloatArray) -> float:
    ax0, ay0 = box_a[0] - box_a[3] / 2.0, box_a[1] - box_a[4] / 2.0
    ax1, ay1 = box_a[0] + box_a[3] / 2.0, box_a[1] + box_a[4] / 2.0
    bx0, by0 = box_b[0] - box_b[3] / 2.0, box_b[1] - box_b[4] / 2.0
    bx1, by1 = box_b[0] + box_b[3] / 2.0, box_b[1] + box_b[4] / 2.0

    inter_x0, inter_y0 = max(ax0, bx0), max(ay0, by0)
    inter_x1, inter_y1 = min(ax1, bx1), min(ay1, by1)
    inter_w, inter_h = max(0.0, inter_x1 - inter_x0), max(0.0, inter_y1 - inter_y0)
    intersection = inter_w * inter_h

    area_a = (ax1 - ax0) * (ay1 - ay0)
    area_b = (bx1 - bx0) * (by1 - by0)
    union = area_a + area_b - intersection
    return float(intersection / max(union, 1e-6))


def compute_detection_map(
    predictions: list[list[DetectionDict]], targets: list[TargetDict], iou_threshold: float
) -> dict[str, float]:
    scores = []
    true_positives = []
    total_gt = sum(len(item["boxes"]) for item in targets)
    if total_gt == 0:
        return {"mAP": 0.0, "precision": 0.0, "recall": 0.0}

    for pred_list, target in zip(predictions, targets):
        gt_boxes = target["boxes"].cpu().numpy()
        gt_labels = target["labels"].cpu().numpy()
        matched = np.zeros(len(gt_boxes), dtype=bool)

        for pred in sorted(pred_list, key=lambda x: x["score"], reverse=True):
            scores.append(pred["score"])
            is_tp = 0.0
            for idx, (gt_box, gt_label) in enumerate(zip(gt_boxes, gt_labels)):
                if matched[idx] or pred["label"] != int(gt_label):
                    continue
                if bev_iou(pred["box"], gt_box) >= iou_threshold:
                    matched[idx] = True
                    is_tp = 1.0
                    break
            true_positives.append(is_tp)

    if not scores:
        return {"mAP": 0.0, "precision": 0.0, "recall": 0.0}

    order = np.argsort(-np.asarray(scores))
    tp = np.asarray(true_positives)[order]
    fp = 1.0 - tp
    cum_tp = np.cumsum(tp)
    cum_fp = np.cumsum(fp)
    precision = cum_tp / np.maximum(cum_tp + cum_fp, 1e-6)
    recall = cum_tp / max(total_gt, 1)
    if len(recall) > 1:
        delta_recall = recall[1:] - recall[:-1]
        avg_precision = (precision[1:] + precision[:-1]) * 0.5
        ap = float(np.sum(avg_precision * delta_recall))
    else:
        ap = float(precision[0] * recall[0])
    return {"mAP": float(ap), "precision": float(precision[-1]), "recall": float(recall[-1])}


def compute_obstacle_distance_error(
    pred_distance: torch.Tensor, target_distance: torch.Tensor, occupancy: torch.Tensor
) -> dict[str, float]:
    mask = occupancy > 0.5
    if mask.sum().item() == 0:
        return {"distance_mae": math.inf}
    error = torch.abs(pred_distance[mask] - target_distance[mask]).mean().item()
    return {"distance_mae": float(error)}


def compute_per_class_detection_metrics(
    predictions: list[list[DetectionDict]],
    targets: list[TargetDict],
    class_names: list[str],
    iou_threshold: float,
) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}

    for class_idx, class_name in enumerate(class_names):
        tp = 0
        fp = 0
        fn = 0
        distance_errors: list[float] = []

        for pred_list, target in zip(predictions, targets):
            gt_boxes = target["boxes"].cpu().numpy()
            gt_labels = target["labels"].cpu().numpy()
            gt_idx = [i for i, lbl in enumerate(gt_labels) if int(lbl) == class_idx]
            pred_cls = [pred for pred in pred_list if int(pred.get("label", -1)) == class_idx]
            matched_gt: set[int] = set()

            for pred in sorted(pred_cls, key=lambda x: x.get("score", 0.0), reverse=True):
                best_gt = None
                best_iou = 0.0
                for gi in gt_idx:
                    if gi in matched_gt:
                        continue
                    iou = bev_iou(pred["box"], gt_boxes[gi])
                    if iou >= iou_threshold and iou > best_iou:
                        best_iou = iou
                        best_gt = gi
                if best_gt is not None:
                    matched_gt.add(best_gt)
                    tp += 1
                    pred_dist = float(np.linalg.norm(np.asarray(pred["box"][:2], dtype=np.float32)))
                    gt_dist = float(
                        np.linalg.norm(np.asarray(gt_boxes[best_gt][:2], dtype=np.float32))
                    )
                    distance_errors.append(abs(pred_dist - gt_dist))
                else:
                    fp += 1

            fn += max(len(gt_idx) - len(matched_gt), 0)

        precision = float(tp / max(tp + fp, 1))
        recall = float(tp / max(tp + fn, 1))
        fnr = float(fn / max(tp + fn, 1))
        metrics[class_name] = {
            "precision": precision,
            "recall": recall,
            "false_negative_rate": fnr,
            "distance_error": float(sum(distance_errors) / len(distance_errors))
            if distance_errors
            else float("inf"),
        }
    return metrics


def compute_dangerous_fnr(
    predictions: list[list[DetectionDict]],
    targets: list[TargetDict],
    dangerous_labels: set[int],
    iou_threshold: float,
) -> dict[str, float]:
    missed = 0
    total = 0

    for pred_list, target in zip(predictions, targets):
        gt_boxes = target["boxes"].cpu().numpy()
        gt_labels = target["labels"].cpu().numpy()
        for gt_box, gt_label in zip(gt_boxes, gt_labels):
            if int(gt_label) not in dangerous_labels:
                continue
            total += 1
            matched = False
            for pred in pred_list:
                if pred["label"] != int(gt_label):
                    continue
                if bev_iou(pred["box"], gt_box) >= iou_threshold:
                    matched = True
                    break
            if not matched:
                missed += 1

    return {"dangerous_fnr": float(missed / max(total, 1))}
