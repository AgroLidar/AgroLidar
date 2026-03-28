"""LiDAR embedding utilities for vector search workflows."""

from __future__ import annotations

import numpy as np


def compute_pointcloud_embedding(points: np.ndarray, embedding_dim: int = 128) -> np.ndarray:
    """Compute a deterministic embedding from LiDAR points.

    This lightweight baseline summarizes geometry and intensity statistics and
    projects them into a fixed-length vector.
    """
    if points.ndim != 2 or points.shape[1] < 3:
        raise ValueError("points must have shape (N, >=3)")

    xyz = points[:, :3].astype(np.float32, copy=False)
    mean = xyz.mean(axis=0)
    std = xyz.std(axis=0)
    mins = xyz.min(axis=0)
    maxs = xyz.max(axis=0)
    base = np.concatenate([mean, std, mins, maxs], axis=0)

    if points.shape[1] > 3:
        intensity = points[:, 3].astype(np.float32, copy=False)
        intensity_stats = np.array([intensity.mean(), intensity.std()], dtype=np.float32)
        base = np.concatenate([base, intensity_stats], axis=0)

    repeats = int(np.ceil(embedding_dim / base.size))
    expanded = np.tile(base, repeats)[:embedding_dim]
    norm = np.linalg.norm(expanded)
    if norm > 0:
        expanded = expanded / norm
    return expanded.astype(np.float32)
