from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

from lidar_perception.data.augmentations import PointCloudAugmentor
from lidar_perception.data.io import load_point_cloud
from lidar_perception.data.preprocessing import AgroPreprocessor, BEVVoxelizer, crop_points


class ReviewedHardCaseDataset(Dataset):
    """Hard-case dataset loader for reviewed mining outputs.

    Supports records from JSON/JSONL/CSV manifests and direct file discovery from
    data/hard_cases and data/review_queue.
    """

    def __init__(self, config: dict, split: str = "train"):
        self.config = config
        self.split = split
        self.class_names = list(config["class_names"])
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}

        self.preprocessor = AgroPreprocessor(config["point_cloud_range"], config.get("preprocessing", {}))
        self.voxelizer = BEVVoxelizer(config["point_cloud_range"], config["grid_size"])
        self.augmentor = PointCloudAugmentor(config["augmentations"]) if split == "train" else None

        hard_cfg = config.get("hard_case", {})
        hard_dirs = hard_cfg.get("dirs", ["data/hard_cases", "data/review_queue"])
        manifest_paths = hard_cfg.get("manifests", [])

        records = self._discover_records(hard_dirs)
        records.extend(self._load_manifest_paths(manifest_paths))
        records = self._dedupe(records)

        only_reviewed = bool(hard_cfg.get("only_reviewed", False))
        only_high_conf_failures = bool(hard_cfg.get("only_high_conf_failures", False))
        min_failure_confidence = float(hard_cfg.get("min_failure_confidence", 0.5))
        self.records = [
            rec
            for rec in records
            if self._include_record(rec, only_reviewed=only_reviewed, only_high_conf_failures=only_high_conf_failures, min_failure_confidence=min_failure_confidence)
        ]

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        rec = self.records[index]
        points = load_point_cloud(rec["point_cloud"])
        points = crop_points(points, self.config["point_cloud_range"]) if points.size else points

        boxes = self._parse_boxes(rec)
        labels = self._parse_labels(rec, len(boxes))

        if self.augmentor is not None:
            points, boxes = self.augmentor(points, boxes)
            points = crop_points(points, self.config["point_cloud_range"])

        points, preprocessing_metadata = self.preprocessor.process(points)
        bev = self.voxelizer.voxelize(points)

        detection_target = self.voxelizer.build_detection_targets(boxes, labels, num_classes=len(self.class_names))
        segmentation_target = self.voxelizer.build_segmentation_target(points, boxes, labels, len(self.config["segmentation_classes"]))
        obstacle_target = self.voxelizer.build_obstacle_targets(points)

        item = {
            "sample_id": rec.get("sample_id", f"hard_{index}"),
            "points": torch.from_numpy(points.astype(np.float32)),
            "bev": torch.from_numpy(bev),
            "boxes": torch.from_numpy(boxes),
            "labels": torch.from_numpy(labels),
            "detection_target": detection_target,
            "segmentation_target": segmentation_target,
            "obstacle_target": obstacle_target,
            "hard_case_metadata": {
                "reviewed": bool(rec.get("reviewed", False)),
                "hazard_score": float(rec.get("hazard_score", 0.0)),
                "uncertainty": float(rec.get("uncertainty", 0.0)),
                "failure_confidence": float(rec.get("failure_confidence", 0.0)),
            },
            "preprocessing_metadata": {
                "filtered_point_count": preprocessing_metadata.filtered_point_count,
                "original_point_count": preprocessing_metadata.original_point_count,
                "vegetation_ratio": preprocessing_metadata.vegetation_ratio,
                "terrain_variation_m": preprocessing_metadata.terrain_variation_m,
            },
        }
        return item

    def _discover_records(self, dirs: list[str]) -> list[dict]:
        records: list[dict] = []
        for dir_str in dirs:
            root = Path(dir_str)
            if not root.exists():
                continue
            for manifest_name in ("manifest.jsonl", "manifest.json", "manifest.csv"):
                path = root / manifest_name
                if path.exists():
                    records.extend(self._load_manifest(path))

            for file in sorted(root.glob("*.json")):
                if file.name.startswith("manifest"):
                    continue
                raw = json.loads(file.read_text(encoding="utf-8"))
                records.append(self._normalize_record(raw, source_path=file))
        return records

    def _load_manifest_paths(self, manifest_paths: list[str]) -> list[dict]:
        rows: list[dict] = []
        for path_str in manifest_paths:
            path = Path(path_str)
            if path.exists():
                rows.extend(self._load_manifest(path))
        return rows

    def _load_manifest(self, path: Path) -> list[dict]:
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            return [self._normalize_record(json.loads(line), source_path=path) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = payload if isinstance(payload, list) else payload.get("records", [])
            return [self._normalize_record(row, source_path=path) for row in rows]
        if suffix == ".csv":
            output: list[dict] = []
            with path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    output.append(self._normalize_record(row, source_path=path))
            return output
        return []

    def _normalize_record(self, raw: dict, source_path: Path) -> dict:
        rec = dict(raw)

        if rec.get("file") and not rec.get("point_cloud"):
            candidate = json.loads(Path(rec["file"]).read_text(encoding="utf-8"))
            rec = {**candidate, **rec}

        point_cloud = rec.get("point_cloud") or rec.get("point_cloud_path") or rec.get("lidar_path")
        if not point_cloud and rec.get("prediction", {}).get("metadata", {}).get("point_cloud"):
            point_cloud = rec["prediction"]["metadata"]["point_cloud"]
        if point_cloud:
            point_path = Path(point_cloud)
            if not point_path.is_absolute():
                point_path = (source_path.parent / point_path).resolve()
            rec["point_cloud"] = str(point_path)

        rec.setdefault("sample_id", source_path.stem)
        rec["reviewed"] = self._as_bool(rec.get("reviewed", rec.get("is_reviewed", False)))
        rec["failure_confidence"] = float(rec.get("failure_confidence", rec.get("score", 0.0)) or 0.0)
        rec["hazard_score"] = float(rec.get("hazard_score", rec.get("hazard", 0.0)) or 0.0)
        rec["uncertainty"] = float(rec.get("uncertainty", rec.get("uncertainty_score", 0.0)) or 0.0)
        return rec

    @staticmethod
    def _as_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return bool(value)

    @staticmethod
    def _dedupe(records: list[dict]) -> list[dict]:
        out: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for rec in records:
            key = (str(rec.get("sample_id", "")), str(rec.get("point_cloud", "")))
            if key in seen:
                continue
            seen.add(key)
            if rec.get("point_cloud"):
                out.append(rec)
        return out

    def _include_record(self, rec: dict, *, only_reviewed: bool, only_high_conf_failures: bool, min_failure_confidence: float) -> bool:
        if only_reviewed and not rec.get("reviewed", False):
            return False
        if only_high_conf_failures and float(rec.get("failure_confidence", 0.0)) < min_failure_confidence:
            return False
        return Path(rec["point_cloud"]).exists()

    def _parse_boxes(self, rec: dict) -> np.ndarray:
        boxes = rec.get("boxes")
        if boxes is None and isinstance(rec.get("ground_truth"), dict):
            boxes = rec["ground_truth"].get("boxes")
        if boxes is None:
            return np.zeros((0, 7), dtype=np.float32)
        arr = np.asarray(boxes, dtype=np.float32)
        if arr.size == 0:
            return np.zeros((0, 7), dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] < 7:
            padded = np.zeros((arr.shape[0], 7), dtype=np.float32)
            padded[:, : arr.shape[1]] = arr
            arr = padded
        return arr[:, :7].astype(np.float32)

    def _parse_labels(self, rec: dict, expected: int) -> np.ndarray:
        labels = rec.get("labels")
        if labels is None and isinstance(rec.get("ground_truth"), dict):
            labels = rec["ground_truth"].get("labels") or rec["ground_truth"].get("class_names")
        if labels is None:
            return np.zeros((expected,), dtype=np.int64)

        if labels and isinstance(labels[0], str):
            mapped = [self.class_to_idx.get(name, 0) for name in labels]
            return np.asarray(mapped[:expected], dtype=np.int64)

        arr = np.asarray(labels, dtype=np.int64).reshape(-1)
        if arr.size < expected:
            arr = np.pad(arr, (0, expected - arr.size), mode="constant")
        return arr[:expected]


class CompositeTrainingDataset(Dataset):
    """Mix base training data with reviewed hard cases using configurable weighting."""

    def __init__(
        self,
        base_dataset: Dataset,
        hard_case_dataset: Dataset,
        *,
        hard_case_ratio: float = 0.3,
        oversample_dangerous_classes: bool = False,
        dangerous_classes: list[int] | None = None,
        dangerous_class_weight: float = 1.5,
        hazard_weighting: bool = True,
        uncertainty_weighting: bool = True,
        seed: int = 42,
    ):
        self.base_dataset = base_dataset
        self.hard_case_dataset = hard_case_dataset
        self.hard_case_ratio = float(np.clip(hard_case_ratio, 0.0, 1.0))
        self.base_ratio = 1.0 - self.hard_case_ratio
        self.oversample_dangerous_classes = oversample_dangerous_classes
        self.dangerous_classes = set(dangerous_classes or [])
        self.dangerous_class_weight = float(max(dangerous_class_weight, 1.0))
        self.hazard_weighting = hazard_weighting
        self.uncertainty_weighting = uncertainty_weighting
        self.rng = np.random.default_rng(seed)
        self.size = max(len(self.base_dataset), len(self.hard_case_dataset), 1)

        self._hard_indices = self._build_weighted_hard_indices()

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, index: int) -> dict:
        choose_hard = self.rng.random() < self.hard_case_ratio and len(self._hard_indices) > 0
        if choose_hard:
            sample = self.hard_case_dataset[int(self.rng.choice(self._hard_indices))]
            sample["dataset_source"] = "hard_case"
            return sample
        sample = self.base_dataset[index % len(self.base_dataset)]
        sample["dataset_source"] = "base"
        return sample

    def _build_weighted_hard_indices(self) -> np.ndarray:
        if len(self.hard_case_dataset) == 0:
            return np.asarray([], dtype=np.int64)

        chosen: list[int] = []
        for idx in range(len(self.hard_case_dataset)):
            sample = self.hard_case_dataset[idx]
            weight = 1.0
            if self.oversample_dangerous_classes:
                labels = sample.get("labels")
                if labels is not None:
                    label_values = labels.tolist() if hasattr(labels, "tolist") else list(labels)
                    if any(int(lbl) in self.dangerous_classes for lbl in label_values):
                        weight *= self.dangerous_class_weight

            meta = sample.get("hard_case_metadata", {})
            if self.hazard_weighting:
                weight *= max(1.0, float(meta.get("hazard_score", 0.0)) + 1.0)
            if self.uncertainty_weighting:
                weight *= max(1.0, float(meta.get("uncertainty", 0.0)) + 1.0)

            repeats = int(np.ceil(weight))
            chosen.extend([idx] * repeats)

        return np.asarray(chosen, dtype=np.int64)

    def composition(self) -> dict:
        return {
            "base_samples": len(self.base_dataset),
            "hard_case_samples": len(self.hard_case_dataset),
            "hard_case_ratio": self.hard_case_ratio,
            "base_ratio": self.base_ratio,
            "weighted_hard_pool_size": int(len(self._hard_indices)),
            "oversample_dangerous_classes": self.oversample_dangerous_classes,
        }
