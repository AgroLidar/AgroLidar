from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from lidar_perception.active_learning.miner import score_candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build active-learning review queue from hard-case manifest")
    parser.add_argument("--config", default="configs/active_learning.yaml")
    parser.add_argument("--hard-manifest", default="data/hard_cases/manifest.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = json.loads(Path(args.config).read_text()) if args.config.endswith(".json") else None
    if cfg is None:
        import yaml

        cfg = yaml.safe_load(Path(args.config).read_text()) or {}
    acfg = cfg.get("active_learning", {})

    queue_dir = Path(acfg.get("review_queue_dir", "data/review_queue"))
    queue_dir.mkdir(parents=True, exist_ok=True)
    out_manifest = Path(acfg.get("manifest_path", "data/review_queue/manifest.jsonl"))

    entries = []
    for line in Path(args.hard_manifest).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        payload = json.loads(Path(rec["file"]).read_text(encoding="utf-8"))
        c = score_candidate(rec["sample_id"], payload["prediction"], acfg)
        entries.append({"sample_id": c.sample_id, "score": c.score, "reasons": c.reasons, "file": rec["file"]})

    entries = sorted(entries, key=lambda x: x["score"], reverse=True)[: int(acfg.get("max_candidates", 200))]
    with out_manifest.open("w", encoding="utf-8") as handle:
        for item in entries:
            handle.write(json.dumps(item) + "\n")
    print(f"review_queue_size={len(entries)} manifest={out_manifest}")


if __name__ == "__main__":
    main()
