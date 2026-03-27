from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

CLASSES = ["human", "animal", "rock", "post", "vehicle"]
CLASS_PROBS = np.array([0.30, 0.20, 0.25, 0.15, 0.10], dtype=np.float64)
FRAME_SHAPE = (4, 512, 512)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic AgroLidar BEV training data")
    parser.add_argument("--output-dir", default="data/")
    parser.add_argument("--train-samples", type=int, default=200)
    parser.add_argument("--val-samples", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _frame_rng_noise(rng: np.random.Generator) -> np.ndarray:
    frame = rng.normal(loc=0.02, scale=0.05, size=FRAME_SHAPE).astype(np.float32)
    frame = np.clip(frame, 0.0, 1.0)
    scatter_count = int(rng.integers(400, 2200))
    xs = rng.integers(0, FRAME_SHAPE[1], size=scatter_count)
    ys = rng.integers(0, FRAME_SHAPE[2], size=scatter_count)
    channels = rng.integers(0, FRAME_SHAPE[0], size=scatter_count)
    frame[channels, xs, ys] = np.clip(frame[channels, xs, ys] + rng.uniform(0.2, 0.9, size=scatter_count), 0.0, 1.0)
    return frame


def _random_object(rng: np.random.Generator, class_name: str) -> dict:
    cx = float(rng.uniform(10.0, 502.0))
    cy = float(rng.uniform(10.0, 502.0))
    w = float(rng.uniform(6.0, 45.0))
    h = float(rng.uniform(6.0, 45.0))
    angle = float(rng.uniform(-np.pi, np.pi))
    distance = float(rng.uniform(1.0, 80.0))
    return {
        "class": class_name,
        "bbox_bev": [cx, cy, w, h, angle],
        "distance_m": distance,
        "confidence_gt": 1.0,
    }


def _write_split(root: Path, split: str, samples: int, rng: np.random.Generator, start_time: datetime) -> Counter:
    frame_dir = root / split / "frames"
    label_dir = root / split / "labels"
    frame_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    counter: Counter = Counter()

    for idx in range(samples):
        frame_id = f"{split}_{idx:05d}"
        frame = _frame_rng_noise(rng)
        np.save(frame_dir / f"{frame_id}.npy", frame)

        object_count = int(rng.integers(0, 6))
        classes = rng.choice(CLASSES, size=object_count, replace=True, p=CLASS_PROBS) if object_count > 0 else []
        objects = []
        for class_name in classes:
            class_name = str(class_name)
            objects.append(_random_object(rng, class_name))
            counter[class_name] += 1

        payload = {
            "frame_id": frame_id,
            "timestamp": (start_time + timedelta(milliseconds=100 * idx)).isoformat(),
            "objects": objects,
        }
        (label_dir / f"{frame_id}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return counter


def main() -> None:
    args = parse_args()
    out = Path(args.output_dir)
    rng = np.random.default_rng(args.seed)
    start = datetime.now(timezone.utc)

    train_counter = _write_split(out, "train", int(args.train_samples), rng, start)
    val_counter = _write_split(out, "val", int(args.val_samples), rng, start + timedelta(hours=1))

    (out / "hard_cases" / "frames").mkdir(parents=True, exist_ok=True)
    (out / "hard_cases" / "labels").mkdir(parents=True, exist_ok=True)
    queue_dir = out / "review_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / "queue.json").write_text("[]\n", encoding="utf-8")
    (queue_dir / "queue_summary.md").write_text("# Review Queue\n\nNo pending hard cases.\n", encoding="utf-8")

    total_counter = train_counter + val_counter
    print(f"generated train_frames={args.train_samples} val_frames={args.val_samples} output_dir={out}")
    for class_name in CLASSES:
        print(f"class={class_name} objects={int(total_counter.get(class_name, 0))}")


if __name__ == "__main__":
    main()
