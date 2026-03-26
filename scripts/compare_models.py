from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path

from lidar_perception.evaluation.model_comparison import compare_models


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare production vs candidate model metrics")
    parser.add_argument("--production-metrics", required=True)
    parser.add_argument("--candidate-metrics", required=True)
    parser.add_argument("--output", default="outputs/reports/model_comparison.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prod = json.loads(Path(args.production_metrics).read_text(encoding="utf-8"))
    cand = json.loads(Path(args.candidate_metrics).read_text(encoding="utf-8"))
    report = compare_models(prod, cand)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"promote={report['promote']} reason={report['decision_reason']} output={out}")


if __name__ == "__main__":
    main()
