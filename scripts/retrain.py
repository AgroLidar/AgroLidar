from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from scripts.train import main as train_main
from lidar_perception.utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline retraining with reviewed hard cases")
    parser.add_argument("--config", default="configs/retrain.yaml")
    parser.add_argument("--resume", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    retrain_cfg = config.get("retrain", {})
    meta = {
        "base_config": args.config,
        "hard_case_manifest": retrain_cfg.get("hard_case_manifest"),
        "hard_case_oversample_ratio": retrain_cfg.get("hard_case_oversample_ratio", 0.0),
        "reviewed_only": retrain_cfg.get("reviewed_only", False),
        "candidate_tag": retrain_cfg.get("candidate_tag", "candidate"),
    }
    meta_path = Path("outputs/reports/retrain_metadata.json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    import sys

    sys.argv = ["scripts/train.py", "--config", args.config] + (["--resume", args.resume] if args.resume else [])
    train_main()


if __name__ == "__main__":
    main()
