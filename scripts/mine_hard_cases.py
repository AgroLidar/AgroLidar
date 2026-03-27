from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml


@dataclass
class MiningConfig:
    confidence_threshold: float
    iou_threshold: float
    dangerous_classes: set[str]
    max_cases_per_run: int
    min_distance_error: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine hard/failure cases from inference outputs")
    parser.add_argument(
        "--inference-dir", required=True, help="Directory with per-frame inference JSON outputs"
    )
    parser.add_argument(
        "--output-dir", default="data/hard_cases/", help="Directory to store mined hard-case files"
    )
    parser.add_argument(
        "--config", default="configs/mining.yaml", help="Mining configuration YAML path"
    )
    return parser.parse_args()


def load_config(path: str) -> MiningConfig:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return MiningConfig(
        confidence_threshold=float(payload.get("confidence_threshold", 0.35)),
        iou_threshold=float(payload.get("iou_threshold", 0.5)),
        dangerous_classes={str(c) for c in payload.get("dangerous_classes", ["human", "animal"])},
        max_cases_per_run=int(payload.get("max_cases_per_run", 500)),
        min_distance_error=float(payload.get("min_distance_error", 2.0)),
    )


def as_xyxy(box: list[float] | tuple[float, ...]) -> tuple[float, float, float, float]:
    if len(box) != 4:
        raise ValueError("bbox must contain exactly 4 numbers")
    x1, y1, a, b = [float(v) for v in box]
    # Supports [x1, y1, x2, y2] and [x, y, w, h].
    if a > x1 and b > y1:
        return x1, y1, a, b
    return x1, y1, x1 + max(0.0, a), y1 + max(0.0, b)


def iou(box_a: list[float] | tuple[float, ...], box_b: list[float] | tuple[float, ...]) -> float:
    ax1, ay1, ax2, ay2 = as_xyxy(box_a)
    bx1, by1, bx2, by2 = as_xyxy(box_b)

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter_area
    if denom <= 0.0:
        return 0.0
    return float(inter_area / denom)


def best_match(
    gt_item: dict[str, Any], detections: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, float]:
    gt_class = str(gt_item.get("class", ""))
    gt_bbox = gt_item.get("bbox", [])

    best_det: dict[str, Any] | None = None
    best_iou = 0.0
    for det in detections:
        if str(det.get("class", "")) != gt_class:
            continue
        det_bbox = det.get("bbox", [])
        try:
            current_iou = iou(gt_bbox, det_bbox)
        except Exception:
            current_iou = 0.0
        if current_iou > best_iou:
            best_iou = current_iou
            best_det = det
    return best_det, best_iou


def safe_distance_error(gt_item: dict[str, Any], det_item: dict[str, Any] | None) -> float:
    gt_distance = gt_item.get("distance")
    det_distance = (det_item or {}).get("distance")
    if gt_distance is None or det_distance is None:
        return math.nan
    try:
        return float(abs(float(gt_distance) - float(det_distance)))
    except (TypeError, ValueError):
        return math.nan


def mine_frame(frame: dict[str, Any], config: MiningConfig) -> list[dict[str, Any]]:
    frame_id = frame.get("frame_id")
    timestamp = frame.get("timestamp")

    detections = [
        d
        for d in frame.get("detections", [])
        if float(d.get("confidence", 0.0)) >= config.confidence_threshold
    ]
    ground_truth = frame.get("ground_truth", [])

    mined: list[dict[str, Any]] = []
    for gt in ground_truth:
        klass = str(gt.get("class", "unknown"))
        matched_det, best_iou = best_match(gt, detections)
        conf = float((matched_det or {}).get("confidence", 0.0))
        distance_error = safe_distance_error(gt, matched_det)

        iou_threshold = config.iou_threshold
        distance_error_threshold = config.min_distance_error
        confidence_threshold = config.confidence_threshold

        # More strict policy for dangerous classes.
        if klass in config.dangerous_classes:
            iou_threshold = min(0.99, iou_threshold + 0.1)
            distance_error_threshold = max(0.0, distance_error_threshold * 0.8)
            confidence_threshold = min(0.99, confidence_threshold + 0.1)

        reason = None
        if best_iou < iou_threshold:
            reason = "low_iou_false_negative"
        elif (not np.isnan(distance_error)) and distance_error > distance_error_threshold:
            reason = "high_distance_error"
        elif matched_det is not None and conf < confidence_threshold:
            reason = "low_confidence_match"

        if reason is None:
            continue

        mined.append(
            {
                "frame_id": frame_id,
                "timestamp": timestamp,
                "class": klass,
                "confidence": round(conf, 6),
                "iou": round(float(best_iou), 6),
                "distance_error": None
                if np.isnan(distance_error)
                else round(float(distance_error), 6),
                "reason": reason,
                "reviewed": False,
            }
        )

    return mined


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    inference_dir = Path(args.inference_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(p for p in inference_dir.glob("*.json") if p.is_file())

    mined_cases: list[dict[str, Any]] = []
    by_class: Counter[str] = Counter()
    by_reason: Counter[str] = Counter()

    for file_path in json_files:
        if len(mined_cases) >= config.max_cases_per_run:
            break
        frame = json.loads(file_path.read_text(encoding="utf-8"))
        frame_mined = mine_frame(frame, config)
        for case in frame_mined:
            if len(mined_cases) >= config.max_cases_per_run:
                break
            mined_cases.append(case)
            by_class[case["class"]] += 1
            by_reason[case["reason"]] += 1

    for idx, case in enumerate(mined_cases, start=1):
        frame_id = case.get("frame_id", f"frame_{idx}")
        klass = case.get("class", "unknown")
        out_name = f"{frame_id}_{klass}_{idx:04d}.json"
        (output_dir / out_name).write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")

    summary = {
        "total_mined": len(mined_cases),
        "by_class": dict(by_class),
        "by_reason": dict(by_reason),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary))


if __name__ == "__main__":
    main()
