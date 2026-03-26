from __future__ import annotations

import torch
from torch import nn


class DetectionHead(nn.Module):
    def __init__(self, in_channels: int, num_classes: int):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
        )
        self.heatmap = nn.Conv2d(in_channels, num_classes, kernel_size=1)
        self.offsets = nn.Conv2d(in_channels, 2, kernel_size=1)
        self.sizes = nn.Conv2d(in_channels, 3, kernel_size=1)
        self.yaw = nn.Conv2d(in_channels, 2, kernel_size=1)
        self.confidence = nn.Conv2d(in_channels, 1, kernel_size=1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        x = self.shared(x)
        return {
            "heatmap": self.heatmap(x),
            "offsets": self.offsets(x),
            "sizes": self.sizes(x),
            "yaw": self.yaw(x),
            "confidence": self.confidence(x),
        }


class SegmentationHead(nn.Module):
    def __init__(self, in_channels: int, num_classes: int):
        super().__init__()
        self.decoder = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels, num_classes, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(x)


class ObstacleHead(nn.Module):
    def __init__(self, in_channels: int):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
        )
        self.occupancy = nn.Conv2d(in_channels, 1, kernel_size=1)
        self.distance = nn.Conv2d(in_channels, 1, kernel_size=1)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        x = self.shared(x)
        return {"occupancy": self.occupancy(x), "distance": self.distance(x)}
