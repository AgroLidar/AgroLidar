from __future__ import annotations

from pathlib import Path

import numpy as np


def load_bin_point_cloud(path: str | Path, num_features: int = 4) -> np.ndarray:
    path = Path(path)
    points = np.fromfile(path, dtype=np.float32)
    if points.size % num_features != 0:
        raise ValueError(f"Invalid .bin point cloud shape for {path}")
    return points.reshape(-1, num_features)


def load_pcd_point_cloud(path: str | Path) -> np.ndarray:
    path = Path(path)
    try:
        import open3d as o3d
    except ImportError as exc:
        raise ImportError("open3d is required to read .pcd files") from exc

    pcd = o3d.io.read_point_cloud(str(path))
    xyz = np.asarray(pcd.points, dtype=np.float32)
    if len(pcd.colors) > 0:
        intensity = np.asarray(pcd.colors, dtype=np.float32).mean(axis=1, keepdims=True)
    else:
        intensity = np.ones((xyz.shape[0], 1), dtype=np.float32)
    return np.concatenate([xyz, intensity], axis=1)


def load_point_cloud(path: str | Path) -> np.ndarray:
    suffix = Path(path).suffix.lower()
    if suffix == ".bin":
        return load_bin_point_cloud(path)
    if suffix == ".pcd":
        return load_pcd_point_cloud(path)
    raise ValueError(f"Unsupported point cloud format: {suffix}")
