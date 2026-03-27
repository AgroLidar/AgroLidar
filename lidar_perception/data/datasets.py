from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
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


class BEVFrameDataset(Dataset):
    """Dataset for preprocessed BEV frames + JSON labels.

    Expects:
      data/<split>/frames/*.npy   shape=(C,H,W), C=4, dtype=float32
      data/<split>/labels/*.json  frame_id/timestamp/objects[] with bbox_bev
    """

    def __init__(self, config: dict, split: str = "train"):
        self.split = split
        self.class_names = list(config["class_names"])
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
        self.max_objects = int(config.get("max_objects", 32))
        self.expected_channels = int(config.get("bev_channels", 4))
        self.expected_height = int(config.get("bev_height", 512))
        self.expected_width = int(config.get("bev_width", 512))
        self.model_height = int(config.get("model_height", config.get("grid_size", [128, 128])[0]))
        self.model_width = int(config.get("model_width", config.get("grid_size", [128, 128])[1]))

        train_dir = Path(config.get("train_dir", "data/train"))
        val_dir = Path(config.get("val_dir", "data/val"))
        test_dir = Path(config.get("test_dir", "data/val"))
        split_map = {"train": train_dir, "val": val_dir, "test": test_dir}
        split_dir = split_map.get(split, test_dir)
        self.frames_dir = split_dir / "frames"
        self.labels_dir = split_dir / "labels"
        if not self.frames_dir.exists():
            raise FileNotFoundError(f"Frames directory not found: {self.frames_dir}")
        if not self.labels_dir.exists():
            raise FileNotFoundError(f"Labels directory not found: {self.labels_dir}")

        self.frame_files = sorted(self.frames_dir.glob("*.npy"))
        self.label_files = {p.stem: p for p in self.labels_dir.glob("*.json")}
        if not self.frame_files:
            raise RuntimeError(f"No .npy frames found under {self.frames_dir}")

    def __len__(self) -> int:
        return len(self.frame_files)

    def _pixel_to_metric(self, px: float, py: float, width: int, height: int) -> tuple[float, float]:
        x = (float(px) / max(width - 1, 1)) * 2.0 - 1.0
        y = (float(py) / max(height - 1, 1)) * 2.0 - 1.0
        return x, y

    def _pixel_size_to_metric(self, w_px: float, h_px: float, width: int, height: int) -> tuple[float, float]:
        return max(float(w_px) / max(width, 1) * 2.0, 1e-3), max(float(h_px) / max(height, 1) * 2.0, 1e-3)

    def _build_targets(self, label_payload: dict, width: int, height: int, det_h: int, det_w: int) -> tuple[torch.Tensor, torch.Tensor, dict]:
        heatmap = np.zeros((len(self.class_names), det_h, det_w), dtype=np.float32)
        offsets = np.zeros((2, det_h, det_w), dtype=np.float32)
        sizes = np.zeros((3, det_h, det_w), dtype=np.float32)
        yaw = np.zeros((2, det_h, det_w), dtype=np.float32)
        mask = np.zeros((1, det_h, det_w), dtype=np.float32)
        segmentation = np.zeros((det_h, det_w), dtype=np.int64)

        objects = label_payload.get("objects", [])[: self.max_objects]
        boxes = []
        labels = []

        for obj in objects:
            class_name = obj.get("class")
            if class_name not in self.class_to_idx:
                continue
            cx, cy, bw, bh, angle = [float(x) for x in obj.get("bbox_bev", [0, 0, 1, 1, 0])]
            gx = int(np.clip((cx / max(width, 1)) * det_h, 0, det_h - 1))
            gy = int(np.clip((cy / max(height, 1)) * det_w, 0, det_w - 1))
            frac_x = (cx / max(width, 1)) * det_h - gx
            frac_y = (cy / max(height, 1)) * det_w - gy
            cls_idx = self.class_to_idx[class_name]

            heatmap[cls_idx, gx, gy] = 1.0
            offsets[:, gx, gy] = np.array([frac_x, frac_y], dtype=np.float32)
            metric_w, metric_h = self._pixel_size_to_metric(bw, bh, width, height)
            sizes[:, gx, gy] = np.array([metric_w, metric_h, 1.0], dtype=np.float32)
            yaw[:, gx, gy] = np.array([np.sin(angle), np.cos(angle)], dtype=np.float32)
            mask[:, gx, gy] = 1.0
            segmentation[gx, gy] = min(cls_idx + 1, len(self.class_names))

            mx, my = self._pixel_to_metric(cx, cy, width, height)
            boxes.append([mx, my, 0.0, metric_w, metric_h, 1.0, angle])
            labels.append(cls_idx)

        obstacle_occupancy = np.where(mask > 0, 1.0, 0.0).astype(np.float32)
        obstacle_distance = np.zeros((1, det_h, det_w), dtype=np.float32)
        if boxes:
            for obj in objects:
                if "distance_m" not in obj:
                    continue
                cx, cy, _, _, _ = [float(x) for x in obj.get("bbox_bev", [0, 0, 1, 1, 0])]
                gx = int(np.clip((cx / max(width, 1)) * det_h, 0, det_h - 1))
                gy = int(np.clip((cy / max(height, 1)) * det_w, 0, det_w - 1))
                obstacle_distance[0, gx, gy] = min(float(obj["distance_m"]) / 80.0, 1.0)

        detection_target = {
            "heatmap": torch.from_numpy(heatmap),
            "offsets": torch.from_numpy(offsets),
            "sizes": torch.from_numpy(sizes),
            "yaw": torch.from_numpy(yaw),
            "mask": torch.from_numpy(mask),
        }
        obstacle_target = {
            "occupancy": torch.from_numpy(obstacle_occupancy),
            "distance": torch.from_numpy(obstacle_distance),
        }
        if boxes:
            boxes_tensor = torch.from_numpy(np.asarray(boxes, dtype=np.float32))
            labels_tensor = torch.from_numpy(np.asarray(labels, dtype=np.int64))
        else:
            boxes_tensor = torch.zeros((0, 7), dtype=torch.float32)
            labels_tensor = torch.zeros((0,), dtype=torch.int64)
        return boxes_tensor, labels_tensor, {
            "detection_target": detection_target,
            "segmentation_target": torch.from_numpy(segmentation),
            "obstacle_target": obstacle_target,
        }

    def __getitem__(self, index: int) -> dict:
        frame_path = self.frame_files[index]
        label_path = self.label_files.get(frame_path.stem)
        if label_path is None:
            raise FileNotFoundError(f"Missing label file for frame '{frame_path.name}' in {self.labels_dir}")

        bev = np.load(frame_path).astype(np.float32)
        if bev.ndim != 3:
            raise ValueError(f"Invalid BEV tensor shape {bev.shape} in {frame_path}")
        c, h, w = bev.shape
        if c != self.expected_channels:
            raise ValueError(f"Expected {self.expected_channels} channels, got {c} in {frame_path}")
        if h != self.expected_height or w != self.expected_width:
            raise ValueError(f"Expected frame shape ({self.expected_height}, {self.expected_width}), got ({h}, {w}) in {frame_path}")
        bev = np.clip(bev, 0.0, 1.0)

        label_payload = json.loads(label_path.read_text(encoding="utf-8"))
        bev_tensor = torch.from_numpy(bev)
        if (h, w) != (self.model_height, self.model_width):
            bev_tensor = F.interpolate(
                bev_tensor.unsqueeze(0),
                size=(self.model_height, self.model_width),
                mode="bilinear",
                align_corners=False,
            ).squeeze(0)
        boxes, labels, targets = self._build_targets(label_payload, w, h, self.model_height, self.model_width)
        return {
            "frame_id": label_payload.get("frame_id", frame_path.stem),
            "timestamp": label_payload.get("timestamp", ""),
            "bev": bev_tensor,
            "points": torch.zeros((0, 4), dtype=torch.float32),
            "boxes": boxes,
            "labels": labels,
            "detection_target": targets["detection_target"],
            "segmentation_target": targets["segmentation_target"],
            "obstacle_target": targets["obstacle_target"],
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
    if dataset_type in {"bev_frame", "bev_frames", "bev"}:
        return BEVFrameDataset(config, split)
    if dataset_type in {"synthetic", "synthetic_agriculture"}:
        return SyntheticLiDARDataset(config, split)
    if dataset_type == "folder":
        return PointCloudFolderDataset(config, split)
    if dataset_type == "manifest":
        return ManifestPointCloudDataset(config, split)
    if dataset_type in {"reviewed_hard_cases", "hard_cases"}:
        return ReviewedHardCaseDataset(config, split)
    raise ValueError(f"Unsupported dataset type: {dataset_type}")
