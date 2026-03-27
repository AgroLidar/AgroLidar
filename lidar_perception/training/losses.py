from __future__ import annotations

import torch
import torch.nn.functional as F


def detection_loss(pred: dict[str, torch.Tensor], target: dict[str, torch.Tensor]) -> torch.Tensor:
    heatmap_loss = F.binary_cross_entropy_with_logits(pred["heatmap"], target["heatmap"])
    mask = target["mask"]
    offset_loss = F.l1_loss(pred["offsets"] * mask, target["offsets"] * mask)
    size_loss = F.l1_loss(pred["sizes"] * mask, target["sizes"] * mask)
    yaw_loss = F.l1_loss(pred["yaw"] * mask, target["yaw"] * mask)
    confidence_target = target["heatmap"].amax(dim=1, keepdim=True)
    confidence_loss = F.binary_cross_entropy_with_logits(pred["confidence"], confidence_target)
    return heatmap_loss + offset_loss + size_loss + yaw_loss + confidence_loss


def segmentation_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return F.cross_entropy(pred, target)


def obstacle_loss(pred: dict[str, torch.Tensor], target: dict[str, torch.Tensor]) -> torch.Tensor:
    occupancy_loss = F.binary_cross_entropy_with_logits(pred["occupancy"], target["occupancy"])
    distance_loss = F.l1_loss(
        torch.sigmoid(pred["distance"]) * target["occupancy"], target["distance"]
    )
    return occupancy_loss + distance_loss
