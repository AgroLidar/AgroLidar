from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path("outputs/registry/registry.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect AgroLidar model registry state")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    parser.add_argument("--production", action="store_true", help="Show only production model")
    parser.add_argument("--history", action="store_true", help="Show all entries ordered by timestamp")
    return parser.parse_args()


def _load_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"Registry not found at {path}. Run the promotion pipeline first.")
        raise SystemExit(0)

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        print(f"Registry at {path} has invalid format (expected a JSON list).")
        raise SystemExit(1)
    return payload


def _sorted_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=lambda item: str(item.get("timestamp", "")), reverse=True)


def _select_entries(entries: list[dict[str, Any]], production_only: bool, history: bool) -> list[dict[str, Any]]:
    ordered = _sorted_entries(entries)

    if production_only:
        production = [entry for entry in ordered if entry.get("status") == "production"]
        return production[:1]

    if history:
        return ordered

    return ordered[:1]


def _metric(entry: dict[str, Any], key: str) -> Any:
    metrics = entry.get("metrics", {})
    if isinstance(metrics, dict):
        return metrics.get(key)
    return None


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _render_table(entries: list[dict[str, Any]]) -> str:
    headers = ["status", "model_tag", "timestamp", "mAP", "dangerous_fnr"]
    rows = []
    for entry in entries:
        rows.append(
            [
                _fmt(entry.get("status")),
                _fmt(entry.get("version") or entry.get("checkpoint")),
                _fmt(entry.get("timestamp")),
                _fmt(_metric(entry, "mAP")),
                _fmt(_metric(entry, "dangerous_fnr")),
            ]
        )

    if not rows:
        return "No matching registry entries."

    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    def fmt_row(values: list[str]) -> str:
        return " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(values))

    divider = "-+-".join("-" * width for width in widths)
    lines = [fmt_row(headers), divider]
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    entries = _load_registry(REGISTRY_PATH)
    selected = _select_entries(entries, production_only=args.production, history=args.history)

    if args.json:
        print(json.dumps(selected, indent=2))
        return 0

    print(_render_table(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
