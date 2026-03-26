from __future__ import annotations

import math

import numpy as np
import torch


def compute_segmentation_iou(logits: torch.Tensor, target: torch.Tensor, num_classes: int) -> dict[str, float]:
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


def bev_iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
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
    return intersection / max(union, 1e-6)


def compute_detection_map(predictions: list[list[dict]], targets: list[dict], iou_threshold: float) -> dict[str, float]:
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
    ap = np.trapz(precision, recall) if len(recall) > 1 else float(precision[0] * recall[0])
    return {"mAP": float(ap), "precision": float(precision[-1]), "recall": float(recall[-1])}


def compute_obstacle_distance_error(pred_distance: torch.Tensor, target_distance: torch.Tensor, occupancy: torch.Tensor) -> dict[str, float]:
    mask = occupancy > 0.5
    if mask.sum().item() == 0:
        return {"distance_mae": math.inf}
    error = torch.abs(pred_distance[mask] - target_distance[mask]).mean().item()
    return {"distance_mae": float(error)}


def compute_dangerous_fnr(predictions: list[list[dict]], targets: list[dict], dangerous_labels: set[int], iou_threshold: float) -> dict[str, float]:
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
