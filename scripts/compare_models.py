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
from lidar_perception.utils.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare production vs candidate model metrics")
    parser.add_argument("--production-metrics", required=True)
    parser.add_argument("--candidate-metrics", required=True)
    parser.add_argument("--config", default="configs/eval.yaml", help="Optional config for comparison policy overrides")
    parser.add_argument("--output", default="outputs/reports/model_comparison.json")
    parser.add_argument("--output-md", default="outputs/reports/model_comparison.md")
    return parser.parse_args()


def render_markdown(report: dict) -> str:
    deltas = report["deltas"]
    lines = [
        "# AgroLidar Model Comparison",
        "",
        f"**Promotion decision:** `{report['promote']}`",
        f"**Reason:** {report['decision_reason']}",
        "",
        "## Safety Deltas",
        "",
        "| Metric | Delta |",
        "|---|---:|",
        f"| recall_gain | {deltas['recall_gain']:.6f} |",
        f"| dangerous_fnr_drop | {deltas['dangerous_fnr_drop']:.6f} |",
        f"| distance_mae_delta | {deltas['distance_mae_delta']:.6f} |",
        f"| latency_regression_ms | {deltas['latency_regression_ms']:.6f} |",
        "",
        "## Dangerous Class Recall Deltas",
        "",
        "| Class | Delta Recall |",
        "|---|---:|",
    ]
    for cls_name, delta in deltas.get("dangerous_class_recall_delta", {}).items():
        lines.append(f"| {cls_name} | {delta:.6f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    compare_cfg = cfg.get("comparison", {})
    prod = json.loads(Path(args.production_metrics).read_text(encoding="utf-8"))
    cand = json.loads(Path(args.candidate_metrics).read_text(encoding="utf-8"))
    report = compare_models(prod, cand, cfg=compare_cfg)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(f"promote={report['promote']} reason={report['decision_reason']} output={out} output_md={out_md}")


if __name__ == "__main__":
    main()
