from __future__ import annotations

from lidar_perception.models.lidar_net import MultiTaskLiDARNet


def build_model(config: dict) -> MultiTaskLiDARNet:
    name = config["name"].lower()
    if name != "pointpillars_bev":
        raise ValueError(f"Unsupported model architecture: {name}")
    return MultiTaskLiDARNet(
        in_channels=int(config["in_channels"]),
        base_channels=int(config["base_channels"]),
        num_classes=int(config["num_classes"]),
        num_segmentation_classes=int(config["num_segmentation_classes"]),
    )
