from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build human review queue from mined hard cases")
    parser.add_argument("--hard-cases-dir", default="data/hard_cases/", help="Directory with mined hard-case JSON files")
    parser.add_argument("--output-dir", default="data/review_queue/", help="Directory to write review queue artifacts")
    parser.add_argument("--config", default="configs/mining.yaml", help="Mining configuration YAML path")
    return parser.parse_args()


def load_config(path: str) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def load_existing_queue_ids(queue_path: Path) -> set[str]:
    if not queue_path.exists():
        return set()
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    ids = set()
    for item in payload:
        ids.add(build_case_id(item))
    return ids


def build_case_id(case: dict[str, Any]) -> str:
    frame_id = str(case.get("frame_id", ""))
    timestamp = str(case.get("timestamp", ""))
    klass = str(case.get("class", ""))
    reason = str(case.get("reason", ""))
    return "::".join([frame_id, timestamp, klass, reason])


def review_priority(case: dict[str, Any], dangerous_classes: set[str]) -> tuple[int, float]:
    klass = str(case.get("class", ""))
    dangerous_priority = 0 if klass in dangerous_classes else 1
    distance_error = case.get("distance_error")
    if distance_error is None:
        distance_error = -1.0
    return dangerous_priority, -float(distance_error)


def to_markdown_table(cases: list[dict[str, Any]]) -> str:
    lines = [
        "# Review Queue Summary",
        "",
        f"Total queued cases: **{len(cases)}**",
        "",
        "| Rank | Frame ID | Timestamp | Class | Reason | Distance Error | IoU | Confidence |",
        "|---:|---|---|---|---|---:|---:|---:|",
    ]
    for idx, item in enumerate(cases, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(idx),
                    str(item.get("frame_id", "")),
                    str(item.get("timestamp", "")),
                    str(item.get("class", "")),
                    str(item.get("reason", "")),
                    str(item.get("distance_error", "")),
                    str(item.get("iou", "")),
                    str(item.get("confidence", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    dangerous_classes = {str(c) for c in cfg.get("dangerous_classes", ["human", "animal"])}

    hard_cases_dir = Path(args.hard_cases_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    queue_path = output_dir / "queue.json"
    summary_path = output_dir / "queue_summary.md"

    existing_queue_ids = load_existing_queue_ids(queue_path)

    candidates: list[dict[str, Any]] = []
    for path in sorted(hard_cases_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        case = json.loads(path.read_text(encoding="utf-8"))
        case_id = build_case_id(case)
        reviewed = bool(case.get("reviewed", False))
        if reviewed:
            continue
        if case_id in existing_queue_ids:
            continue
        case["case_id"] = case_id
        candidates.append(case)

    ordered = sorted(candidates, key=lambda c: review_priority(c, dangerous_classes))

    queue_path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(to_markdown_table(ordered), encoding="utf-8")

    print(f"queued={len(ordered)} queue={queue_path} summary={summary_path}")


if __name__ == "__main__":
    main()
