from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from lidar_perception.data.datasets import build_dataset
from lidar_perception.evaluation.failure_mining import identify_failures
from lidar_perception.inference.runtime import InferenceRuntime
from lidar_perception.utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine hard/failure cases from inference outputs")
    parser.add_argument("--config", default="configs/active_learning.yaml")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--split", default="test")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    runtime = InferenceRuntime(args.config, args.checkpoint)
    dataset = build_dataset(config["data"], split=args.split)
    hard_dir = Path("data/hard_cases")
    hard_dir.mkdir(parents=True, exist_ok=True)
    manifest = hard_dir / "manifest.jsonl"

    thresholds = {"low_confidence": 0.25, "near_miss_distance_m": 8.0, "distance_error_m": 5.0}
    kept = 0
    with manifest.open("w", encoding="utf-8") as handle:
        for idx in range(len(dataset)):
            sample = dataset[idx]
            result = runtime.infer_points(sample["points"].numpy())
            reasons = identify_failures(result, thresholds)
            if reasons:
                record = {"sample_id": f"{args.split}_{idx}", "reasons": reasons, "prediction": result}
                out = hard_dir / f"{args.split}_{idx}.json"
                out.write_text(json.dumps(record, indent=2, default=lambda x: x.tolist() if hasattr(x, "tolist") else x) + "\n", encoding="utf-8")
                handle.write(json.dumps({"sample_id": record["sample_id"], "reasons": reasons, "file": str(out)}) + "\n")
                kept += 1
    print(f"mined_hard_cases={kept} manifest={manifest}")


if __name__ == "__main__":
    main()
