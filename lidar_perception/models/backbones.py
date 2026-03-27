from __future__ import annotations

import torch
from torch import nn


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(
                in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class BEVBackbone(nn.Module):
    def __init__(self, in_channels: int, base_channels: int):
        super().__init__()
        self.stem = ConvBlock(in_channels, base_channels)
        self.layer1 = ConvBlock(base_channels, base_channels * 2, stride=2)
        self.layer2 = ConvBlock(base_channels * 2, base_channels * 4, stride=2)

        self.up1 = nn.Sequential(
            nn.ConvTranspose2d(
                base_channels * 2, base_channels, kernel_size=2, stride=2, bias=False
            ),
            nn.BatchNorm2d(base_channels),
            nn.ReLU(inplace=True),
        )
        self.up2 = nn.Sequential(
            nn.ConvTranspose2d(
                base_channels * 4, base_channels, kernel_size=4, stride=4, bias=False
            ),
            nn.BatchNorm2d(base_channels),
            nn.ReLU(inplace=True),
        )
        self.fusion = ConvBlock(base_channels * 3, base_channels * 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x0 = self.stem(x)
        x1 = self.layer1(x0)
        x2 = self.layer2(x1)
        fused = torch.cat([x0, self.up1(x1), self.up2(x2)], dim=1)
        return self.fusion(fused)
