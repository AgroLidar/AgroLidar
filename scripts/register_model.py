from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from lidar_perception.registry.model_registry import ModelRegistry, new_entry
from lidar_perception.utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register model artifact in lightweight registry")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--status", choices=["candidate", "production", "archived"], default="candidate")
    parser.add_argument("--version", required=True)
    parser.add_argument("--dataset-manifest", default="data/manifests/train_manifest.json")
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    registry = ModelRegistry("outputs/registry")
    entry = new_entry(args.version, args.status, args.checkpoint, cfg, args.dataset_manifest, metrics, notes=args.notes)
    created = registry.add(entry)
    print(json.dumps(created, indent=2))


if __name__ == "__main__":
    main()
