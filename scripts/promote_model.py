from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import json
from datetime import datetime, timezone

from lidar_perception.registry.model_registry import ModelRegistry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote/reject candidate model based on comparison report")
    parser.add_argument("--candidate-model", required=True)
    parser.add_argument("--production-model", required=True)
    parser.add_argument("--comparison-report", required=True)
    parser.add_argument("--registry-dir", default="outputs/registry")
    parser.add_argument("--candidate-version", default=None)
    parser.add_argument("--production-version", default=None)
    return parser.parse_args()


def _latest_with_checkpoint(entries: list[dict], checkpoint: str, status: str | None = None) -> dict | None:
    matches = [e for e in entries if e.get("checkpoint") == checkpoint and (status is None or e.get("status") == status)]
    if not matches:
        return None
    return sorted(matches, key=lambda x: x.get("timestamp", ""))[-1]


def main() -> None:
    args = parse_args()
    report = json.loads(Path(args.comparison_report).read_text(encoding="utf-8"))

    registry = ModelRegistry(args.registry_dir)
    entries = registry.list_entries()

    now = datetime.now(timezone.utc).isoformat()
    candidate = _latest_with_checkpoint(entries, args.candidate_model, status="candidate")
    production = _latest_with_checkpoint(entries, args.production_model, status="production")

    if report.get("promote", False):
        if production is not None:
            production["status"] = "archived"
            production["notes"] = (production.get("notes", "") + f" | archived_at={now} promoted_candidate={args.candidate_model}").strip()
        if candidate is not None:
            candidate["status"] = "production"
            candidate["notes"] = (candidate.get("notes", "") + f" | promoted_at={now}").strip()
        else:
            entries.append(
                {
                    "version": args.candidate_version or f"candidate-{now}",
                    "timestamp": now,
                    "status": "production",
                    "checkpoint": args.candidate_model,
                    "config_hash": "",
                    "dataset_manifest": "",
                    "metrics": report.get("candidate", {}),
                    "notes": f"promoted_from_report={args.comparison_report}",
                }
            )
        decision = "accepted"
    else:
        if candidate is not None:
            candidate["status"] = "rejected"
            candidate["notes"] = (candidate.get("notes", "") + f" | rejected_at={now} reason={report.get('decision_reason', 'policy_failed')}").strip()
        else:
            entries.append(
                {
                    "version": args.candidate_version or f"candidate-{now}",
                    "timestamp": now,
                    "status": "rejected",
                    "checkpoint": args.candidate_model,
                    "config_hash": "",
                    "dataset_manifest": "",
                    "metrics": report.get("candidate", {}),
                    "notes": f"rejected_from_report={args.comparison_report} reason={report.get('decision_reason', 'policy_failed')}",
                }
            )
        decision = "rejected"

    Path(args.registry_dir).mkdir(parents=True, exist_ok=True)
    (Path(args.registry_dir) / "registry.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"promotion_decision={decision} registry={Path(args.registry_dir) / 'registry.json'}")


if __name__ == "__main__":
    main()
