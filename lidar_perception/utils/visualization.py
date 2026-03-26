from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def visualize_bev(points: np.ndarray, detections: list[dict], save_path: str | Path | None = None) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(points[:, 0], points[:, 1], s=1, c=points[:, 2], cmap="viridis")
    for det in detections:
        cx, cy, _, dx, dy, _, _ = det["box"]
        rect = plt.Rectangle((cx - dx / 2.0, cy - dy / 2.0), dx, dy, fill=False, edgecolor="red", linewidth=2)
        ax.add_patch(rect)
        ax.text(cx, cy, f"{det['label']}:{det['score']:.2f}", color="white", fontsize=8, bbox={"facecolor": "red", "alpha": 0.5})
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("LiDAR BEV Predictions")
    ax.set_aspect("equal")
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


def visualize_open3d(points: np.ndarray, detections: list[dict]) -> None:
    try:
        import open3d as o3d
    except ImportError as exc:
        raise ImportError("open3d is required for 3D visualization") from exc

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points[:, :3])
    geometries = [cloud]

    for det in detections:
        cx, cy, cz, dx, dy, dz, _ = det["box"]
        bbox = o3d.geometry.AxisAlignedBoundingBox(
            min_bound=(cx - dx / 2.0, cy - dy / 2.0, cz - dz / 2.0),
            max_bound=(cx + dx / 2.0, cy + dy / 2.0, cz + dz / 2.0),
        )
        bbox.color = (1.0, 0.0, 0.0)
        geometries.append(bbox)

    o3d.visualization.draw_geometries(geometries)
