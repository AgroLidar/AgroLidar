from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

from lidar_perception.data.augmentations import PointCloudAugmentor
from lidar_perception.data.io import load_point_cloud
from lidar_perception.data.preprocessing import AgroPreprocessor, BEVVoxelizer, crop_points
from lidar_perception.data.hard_case_dataset import ReviewedHardCaseDataset
from lidar_perception.simulation.agricultural_scene import AgriculturalSceneGenerator


class SyntheticLiDARDataset(Dataset):
    def __init__(self, config: dict, split: str):
        self.config = config
        self.split = split
        self.size = int(config[f"{split}_size"])
        self.num_points = int(config["num_points"])
        self.class_names = list(config["class_names"])
        self.max_objects = int(config["max_objects"])
        self.preprocessor = AgroPreprocessor(config["point_cloud_range"], config.get("preprocessing", {}))
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
        points, preprocessing_metadata = self.preprocessor.process(points)

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
            "preprocessing_metadata": {
                "filtered_point_count": preprocessing_metadata.filtered_point_count,
                "original_point_count": preprocessing_metadata.original_point_count,
                "vegetation_ratio": preprocessing_metadata.vegetation_ratio,
                "terrain_variation_m": preprocessing_metadata.terrain_variation_m,
            },
        }


class PointCloudFolderDataset(Dataset):
    def __init__(self, config: dict, split: str = "test"):
        self.root_dir = Path(config["root_dir"])
        self.preprocessor = AgroPreprocessor(config["point_cloud_range"], config.get("preprocessing", {}))
        self.voxelizer = BEVVoxelizer(config["point_cloud_range"], config["grid_size"])
        self.files = sorted([p for p in self.root_dir.glob("**/*") if p.suffix.lower() in {".bin", ".pcd"}])
        self.split = split

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        path = self.files[index]
        points, preprocessing_metadata = self.preprocessor.process(load_point_cloud(path))
        bev = self.voxelizer.voxelize(points)
        return {
            "path": str(path),
            "points": torch.from_numpy(points.astype(np.float32)),
            "bev": torch.from_numpy(bev),
            "preprocessing_metadata": {
                "filtered_point_count": preprocessing_metadata.filtered_point_count,
                "original_point_count": preprocessing_metadata.original_point_count,
                "vegetation_ratio": preprocessing_metadata.vegetation_ratio,
                "terrain_variation_m": preprocessing_metadata.terrain_variation_m,
            },
        }


class ManifestPointCloudDataset(Dataset):
    """Dataset wrapper for future real tractor logs via JSONL manifest.

    Each manifest row supports: {"point_cloud": "...bin|pcd", "metadata": {...}}.
    """

    def __init__(self, config: dict, split: str = "train"):
        manifest_key = f"{split}_manifest"
        manifest_path = Path(config.get(manifest_key) or config.get("manifest_path", ""))
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        self.records = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.preprocessor = AgroPreprocessor(config["point_cloud_range"], config.get("preprocessing", {}))
        self.voxelizer = BEVVoxelizer(config["point_cloud_range"], config["grid_size"])

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict:
        rec = self.records[index]
        points = load_point_cloud(rec["point_cloud"])
        points, metadata = self.preprocessor.process(points)
        bev = self.voxelizer.voxelize(points)
        return {
            "sample_id": rec.get("sample_id", f"manifest_{index}"),
            "path": rec["point_cloud"],
            "points": torch.from_numpy(points.astype(np.float32)),
            "bev": torch.from_numpy(bev),
            "metadata": rec.get("metadata", {}),
            "preprocessing_metadata": {
                "filtered_point_count": metadata.filtered_point_count,
                "original_point_count": metadata.original_point_count,
                "vegetation_ratio": metadata.vegetation_ratio,
                "terrain_variation_m": metadata.terrain_variation_m,
            },
        }


def collate_fn(batch: list[dict]) -> dict:
    bev = torch.stack([item["bev"] for item in batch], dim=0)
    points = [item["points"] for item in batch]
    result = {"bev": bev, "points": points}

    if "path" in batch[0]:
        result["path"] = [item["path"] for item in batch]
    if "sample_id" in batch[0]:
        result["sample_id"] = [item["sample_id"] for item in batch]
    if "metadata" in batch[0]:
        result["metadata"] = [item["metadata"] for item in batch]
    if "preprocessing_metadata" in batch[0]:
        result["preprocessing_metadata"] = [item["preprocessing_metadata"] for item in batch]
    if "hard_case_metadata" in batch[0]:
        result["hard_case_metadata"] = [item["hard_case_metadata"] for item in batch]
    if "dataset_source" in batch[0]:
        result["dataset_source"] = [item["dataset_source"] for item in batch]

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
    if dataset_type == "manifest":
        return ManifestPointCloudDataset(config, split)
    if dataset_type in {"reviewed_hard_cases", "hard_cases"}:
        return ReviewedHardCaseDataset(config, split)
    raise ValueError(f"Unsupported dataset type: {dataset_type}")
