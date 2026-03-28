from __future__ import annotations

from pathlib import Path

import torch

from lidar_perception.models.backbones import BEVBackbone
from lidar_perception.models.base import BasePerceptionModel
from lidar_perception.models.heads import DetectionHead, ObstacleHead, SegmentationHead


class MultiTaskLiDARNet(BasePerceptionModel):
    """Multi-task BEV perception model for detection, segmentation, and obstacle distance."""

    def __init__(
        self, in_channels: int, base_channels: int, num_classes: int, num_segmentation_classes: int
    ):
        """Initialize model backbone and prediction heads.

        Args:
            in_channels: Number of BEV feature input channels.
            base_channels: Backbone base channel width.
            num_classes: Number of object detection classes.
            num_segmentation_classes: Number of semantic segmentation classes.
        """
        super().__init__()
        self.backbone = BEVBackbone(in_channels=in_channels, base_channels=base_channels)
        head_channels = base_channels * 2
        self.detection_head = DetectionHead(head_channels, num_classes)
        self.segmentation_head = SegmentationHead(head_channels, num_segmentation_classes)
        self.obstacle_head = ObstacleHead(head_channels)

    def forward(self, bev: torch.Tensor) -> dict[str, torch.Tensor | dict[str, torch.Tensor]]:
        """Run forward pass.

        Args:
            bev: Input BEV tensor.

        Returns:
            Dictionary with detection, segmentation, and obstacle head outputs.
        """
        features = self.backbone(bev)
        return {
            "detection": self.detection_head(features),
            "segmentation": self.segmentation_head(features),
            "obstacle": self.obstacle_head(features),
        }

    def predict(self, bev: torch.Tensor) -> dict[str, torch.Tensor | dict[str, torch.Tensor]]:
        """Run prediction alias for ``forward``.

        Args:
            bev: Input BEV tensor.

        Returns:
            Raw task heads output dictionary.
        """
        return self.forward(bev)

    def export_onnx(self, output_path: str | Path, sample_input: torch.Tensor) -> Path:
        """Export model in ONNX format.

        Args:
            output_path: Output ONNX file path.
            sample_input: Sample input tensor for export tracing.

        Returns:
            Final ONNX model path.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.eval()
        torch.onnx.export(self, sample_input, str(path), opset_version=17)
        return path

    def get_safety_metrics(self) -> dict[str, float]:
        """Return architecture-level default safety metric placeholders.

        Returns:
            A mapping of expected safety metric keys to default values.
        """
        return {
            "dangerous_class_recall": 0.0,
            "dangerous_class_fnr": 1.0,
        }
