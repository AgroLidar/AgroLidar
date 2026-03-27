from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def visualize_bev(
    points: np.ndarray,
    detections: list[dict],
    save_path: str | Path | None = None,
    filtered_points: np.ndarray | None = None,
    corridor_width_m: float | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(
        points[:, 0], points[:, 1], s=1, c=points[:, 2], cmap="Greys", alpha=0.35, label="raw"
    )
    if filtered_points is not None and filtered_points.size > 0:
        ax.scatter(
            filtered_points[:, 0],
            filtered_points[:, 1],
            s=1,
            c=filtered_points[:, 2],
            cmap="viridis",
            alpha=0.8,
            label="filtered",
        )
    if corridor_width_m is not None:
        ax.axhline(corridor_width_m, color="orange", linestyle="--", linewidth=1)
        ax.axhline(-corridor_width_m, color="orange", linestyle="--", linewidth=1)
    for det in detections:
        cx, cy, _, dx, dy, _, _ = det["box"]
        color = {"emergency": "red", "warning": "yellow", "monitor": "cyan"}.get(
            det.get("risk_level", "monitor"), "red"
        )
        rect = plt.Rectangle(
            (cx - dx / 2.0, cy - dy / 2.0), dx, dy, fill=False, edgecolor=color, linewidth=2
        )
        ax.add_patch(rect)
        label_text = det.get("label_name", det["label"])
        ax.text(
            cx,
            cy,
            f"{label_text}:{det['score']:.2f}|{det.get('risk_level', 'monitor')}",
            color="white",
            fontsize=8,
            bbox={"facecolor": color, "alpha": 0.6},
        )
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("LiDAR BEV Predictions")
    ax.set_aspect("equal")
    ax.legend(loc="upper right")
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


def visualize_open3d(
    points: np.ndarray, detections: list[dict], filtered_points: np.ndarray | None = None
) -> None:
    try:
        import open3d as o3d
    except ImportError as exc:
        raise ImportError("open3d is required for 3D visualization") from exc

    cloud = o3d.geometry.PointCloud()
    base_points = (
        filtered_points if filtered_points is not None and filtered_points.size > 0 else points
    )
    cloud.points = o3d.utility.Vector3dVector(base_points[:, :3])
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
