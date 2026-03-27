from __future__ import annotations

import torch
from torch import nn

from lidar_perception.models.backbones import BEVBackbone
from lidar_perception.models.heads import DetectionHead, ObstacleHead, SegmentationHead


class MultiTaskLiDARNet(nn.Module):
    def __init__(
        self, in_channels: int, base_channels: int, num_classes: int, num_segmentation_classes: int
    ):
        super().__init__()
        self.backbone = BEVBackbone(in_channels=in_channels, base_channels=base_channels)
        head_channels = base_channels * 2
        self.detection_head = DetectionHead(head_channels, num_classes)
        self.segmentation_head = SegmentationHead(head_channels, num_segmentation_classes)
        self.obstacle_head = ObstacleHead(head_channels)

    def forward(self, bev: torch.Tensor) -> dict[str, torch.Tensor | dict[str, torch.Tensor]]:
        features = self.backbone(bev)
        return {
            "detection": self.detection_head(features),
            "segmentation": self.segmentation_head(features),
            "obstacle": self.obstacle_head(features),
        }
