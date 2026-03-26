from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

from lidar_perception.data.augmentations import PointCloudAugmentor
from lidar_perception.data.io import load_point_cloud
from lidar_perception.data.preprocessing import BEVVoxelizer, crop_points
from lidar_perception.simulation.agricultural_scene import AgriculturalSceneGenerator


class SyntheticLiDARDataset(Dataset):
    def __init__(self, config: dict, split: str):
        self.config = config
        self.split = split
        self.size = int(config[f"{split}_size"])
        self.num_points = int(config["num_points"])
        self.class_names = list(config["class_names"])
        self.max_objects = int(config["max_objects"])
        self.voxelizer = BEVVoxelizer(config["point_cloud_range"], config["grid_size"])
        self.augmentor = PointCloudAugmentor(config["augmentations"]) if split == "train" else None
        self.rng = np.random.default_rng(42 + {"train": 0, "val": 1000, "test": 2000}[split])
        self.generator = AgriculturalSceneGenerator(config, self.rng)

    def __len__(self) -> int:
        return self.size

    def _generate_scene(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        point_cloud, boxes, labels = self.generator.generate(self.num_points, self.max_objects)
        point_cloud = crop_points(point_cloud, self.config["point_cloud_range"])
        return point_cloud.astype(np.float32), boxes, labels

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        points, boxes, labels = self._generate_scene()
        if self.augmentor is not None:
            points, boxes = self.augmentor(points, boxes)
            points = crop_points(points, self.config["point_cloud_range"])

        bev = self.voxelizer.voxelize(points)
        detection_target = self.voxelizer.build_detection_targets(boxes, labels, num_classes=len(self.class_names))
        segmentation_target = self.voxelizer.build_segmentation_target(points, boxes, labels, len(self.config["segmentation_classes"]))
        obstacle_target = self.voxelizer.build_obstacle_targets(points)

        return {
            "points": torch.from_numpy(points.astype(np.float32)),
            "bev": torch.from_numpy(bev),
            "boxes": torch.from_numpy(boxes),
            "labels": torch.from_numpy(labels),
            "detection_target": detection_target,
            "segmentation_target": segmentation_target,
            "obstacle_target": obstacle_target,
        }


class PointCloudFolderDataset(Dataset):
    def __init__(self, config: dict, split: str = "test"):
        self.root_dir = Path(config["root_dir"])
        self.voxelizer = BEVVoxelizer(config["point_cloud_range"], config["grid_size"])
        self.files = sorted([p for p in self.root_dir.glob("**/*") if p.suffix.lower() in {".bin", ".pcd"}])
        self.split = split

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        path = self.files[index]
        points = crop_points(load_point_cloud(path), self.voxelizer.point_cloud_range)
        bev = self.voxelizer.voxelize(points)
        return {
            "path": str(path),
            "points": torch.from_numpy(points.astype(np.float32)),
            "bev": torch.from_numpy(bev),
        }


def collate_fn(batch: list[dict]) -> dict:
    bev = torch.stack([item["bev"] for item in batch], dim=0)
    points = [item["points"] for item in batch]
    result = {"bev": bev, "points": points}

    if "path" in batch[0]:
        result["path"] = [item["path"] for item in batch]

    if "boxes" in batch[0]:
        result["boxes"] = [item["boxes"] for item in batch]
        result["labels"] = [item["labels"] for item in batch]
        result["detection_target"] = {
            key: torch.stack([item["detection_target"][key] for item in batch], dim=0)
            for key in batch[0]["detection_target"].keys()
        }
        result["segmentation_target"] = torch.stack([item["segmentation_target"] for item in batch], dim=0)
        result["obstacle_target"] = {
            key: torch.stack([item["obstacle_target"][key] for item in batch], dim=0)
            for key in batch[0]["obstacle_target"].keys()
        }

    return result


def build_dataset(config: dict, split: str) -> Dataset:
    dataset_type = config["dataset_type"].lower()
    if dataset_type in {"synthetic", "synthetic_agriculture"}:
        return SyntheticLiDARDataset(config, split)
    if dataset_type == "folder":
        return PointCloudFolderDataset(config, split)
    raise ValueError(f"Unsupported dataset type: {dataset_type}")
