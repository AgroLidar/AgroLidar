from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate historical safety regression report")
    parser.add_argument("--runs-dir", default="mlruns/", help="MLflow runs directory")
    parser.add_argument("--n-last", type=int, default=10, help="Number of latest runs")
    parser.add_argument(
        "--output",
        default="outputs/reports/regression_history.md",
        help="Output markdown report path",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _metric(run_dir: Path, name: str) -> float | None:
    metric_path = run_dir / "metrics" / name
    if not metric_path.exists():
        return None
    lines = [
        ln.strip() for ln in metric_path.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    if not lines:
        return None
    try:
        return float(lines[-1].split()[-1])
    except (TypeError, ValueError, IndexError):
        return None


def _load_mlruns(runs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not runs_dir.exists():
        return rows

    for run_meta in runs_dir.glob("*/**/meta.yaml"):
        run_dir = run_meta.parent
        tags_dir = run_dir / "tags"
        run_type = (
            (tags_dir / "run_type").read_text(encoding="utf-8").strip()
            if (tags_dir / "run_type").exists()
            else ""
        )
        if run_type != "evaluation":
            continue

        meta = yaml.safe_load(run_meta.read_text(encoding="utf-8")) or {}
        if not isinstance(meta, dict):
            continue

        per_human = _metric(run_dir, "eval/recall_human")
        per_animal = _metric(run_dir, "eval/recall_animal")
        gate = "UNKNOWN"

        rows.append(
            {
                "run": str(meta.get("run_id") or run_dir.name),
                "date": _from_ms(meta.get("end_time") or meta.get("start_time")),
                "mAP": _metric(run_dir, "eval/mAP"),
                "human_recall": per_human,
                "animal_recall": per_animal,
                "dangerous_fnr": _metric(run_dir, "eval/dangerous_fnr"),
                "latency_ms": _metric(run_dir, "eval/latency_ms")
                or _metric(run_dir, "eval/latency"),
                "gate": gate,
            }
        )
    return sorted(rows, key=lambda x: x["date"], reverse=True)


def _from_ms(value: Any) -> str:
    try:
        ts = int(value) / 1000.0
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat()
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_from_outputs(outputs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not outputs_dir.exists():
        return rows

    for report_path in outputs_dir.glob("*eval*.json"):
        report = _read_json(report_path)
        if not report:
            continue
        per = report.get("per_class", {}) if isinstance(report.get("per_class"), dict) else {}
        gate_report = _read_json(outputs_dir / "gate_report.json") or {}
        rows.append(
            {
                "run": report_path.stem,
                "date": datetime.fromtimestamp(
                    report_path.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                "mAP": report.get("mAP"),
                "human_recall": (per.get("human") or {}).get("recall"),
                "animal_recall": (per.get("animal") or {}).get("recall"),
                "dangerous_fnr": report.get("dangerous_fnr"),
                "latency_ms": report.get("latency_ms", report.get("latency")),
                "gate": gate_report.get("decision", "UNKNOWN"),
            }
        )
    return sorted(rows, key=lambda x: x["date"], reverse=True)


def _trend(rows: list[dict[str, Any]], key: str) -> str:
    vals = [r.get(key) for r in rows if isinstance(r.get(key), (int, float))]
    if len(vals) < 2:
        return "→ stable"
    delta = vals[0] - vals[-1]
    if abs(delta) < 1e-6:
        return "→ stable"
    direction = "↑ regressing" if delta > 0 else "↓ improving"
    if key in {"mAP", "human_recall", "animal_recall"}:
        direction = "↑ improving" if delta > 0 else "↓ regressing"
    return direction


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return "n/a"
    return str(value)


def render_markdown(rows: list[dict[str, Any]], n_last: int) -> str:
    selected = rows[:n_last]
    lines = [
        f"# AgroLidar Regression History (last {n_last} runs)",
        "",
        "| Run | Date | mAP | human_recall | animal_recall | dangerous_fnr | latency_ms | Gate |",
        "|-----|------|-----|--------------|---------------|---------------|------------|------|",
    ]
    for row in selected:
        lines.append(
            "| {run} | {date} | {mAP} | {human_recall} | {animal_recall} | {dangerous_fnr} | {latency_ms} | {gate} |".format(
                run=row["run"],
                date=row["date"],
                mAP=_fmt(row.get("mAP")),
                human_recall=_fmt(row.get("human_recall")),
                animal_recall=_fmt(row.get("animal_recall")),
                dangerous_fnr=_fmt(row.get("dangerous_fnr")),
                latency_ms=_fmt(row.get("latency_ms")),
                gate=row.get("gate", "UNKNOWN"),
            )
        )

    lines += [
        "",
        "## Trend Analysis",
        f"- dangerous_fnr: {_trend(selected, 'dangerous_fnr')}",
        f"- human_recall: {_trend(selected, 'human_recall')}",
        f"- mAP: {_trend(selected, 'mAP')}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    runs = _load_mlruns(Path(args.runs_dir))
    if not runs:
        runs = _load_from_outputs(Path("outputs/reports"))

    report_md = render_markdown(runs, args.n_last)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md, encoding="utf-8")

    print(f"regression_report_written={output_path} rows={min(len(runs), args.n_last)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
