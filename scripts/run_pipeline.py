from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("pipeline")


class PipelineError(RuntimeError):
    """Raised when a pipeline step fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run full AgroLidar training-to-promotion pipeline"
    )
    parser.add_argument(
        "--config-dir",
        default="configs",
        help="Directory containing train.yaml/retrain.yaml/eval.yaml",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run pipeline without promotion/registry writes"
    )
    parser.add_argument(
        "--candidate-tag",
        default=None,
        help="Optional candidate tag to evaluate/promote from outputs/candidates/<tag>/checkpoints/best.pt",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging")
    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(message)s")


def read_json(path: Path) -> dict[str, Any] | list[Any]:
    if not path.exists():
        raise FileNotFoundError(f"Expected JSON output not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_step(name: str, cmd: list[str]) -> None:
    LOGGER.info("▶ Running step '%s': %s", name, " ".join(cmd))
    try:
        completed = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise PipelineError(f"Step '{name}' failed with exit code {exc.returncode}") from exc
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise PipelineError(f"Step '{name}' raised exception: {exc}") from exc

    LOGGER.debug("Step '%s' finished with code %s", name, completed.returncode)


def summarize_train(metrics_jsonl: Path) -> None:
    if not metrics_jsonl.exists():
        LOGGER.info("train summary unavailable (missing %s)", metrics_jsonl)
        return

    lines = [
        line for line in metrics_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not lines:
        LOGGER.info("train summary unavailable (%s is empty)", metrics_jsonl)
        return

    last = json.loads(lines[-1])
    epoch = last.get("epoch")
    train_loss = last.get("train", {}).get("loss")
    val = last.get("val", {})
    LOGGER.info(
        "train summary | epoch=%s train_loss=%s val_mAP=%s val_dangerous_fnr=%s",
        epoch,
        _fmt(train_loss),
        _fmt(val.get("mAP")),
        _fmt(val.get("dangerous_fnr")),
    )


def summarize_retrain(meta_path: Path) -> dict[str, Any]:
    payload = read_json(meta_path)
    if not isinstance(payload, dict):
        raise PipelineError(f"Unexpected retrain metadata format in {meta_path}")

    LOGGER.info(
        "retrain summary | candidate_output_dir=%s hard_cases_used=%s hard_case_ratio=%s",
        payload.get("candidate_output_dir"),
        payload.get("hard_cases_used"),
        _fmt(payload.get("hard_case_ratio")),
    )
    return payload


def summarize_evaluate(report_path: Path, label: str) -> dict[str, Any]:
    payload = read_json(report_path)
    if not isinstance(payload, dict):
        raise PipelineError(f"Unexpected evaluation report format in {report_path}")

    LOGGER.info(
        "%s eval summary | mAP=%s dangerous_fnr=%s recall=%s latency_ms=%s",
        label,
        _fmt(payload.get("mAP")),
        _fmt(payload.get("dangerous_fnr")),
        _fmt(payload.get("recall")),
        _fmt(payload.get("latency_ms")),
    )
    return payload


def summarize_compare(report_path: Path) -> dict[str, Any]:
    payload = read_json(report_path)
    if not isinstance(payload, dict):
        raise PipelineError(f"Unexpected comparison report format in {report_path}")

    deltas = payload.get("deltas", {})
    LOGGER.info(
        "compare summary | promote=%s reason=%s recall_gain=%s dangerous_fnr_drop=%s",
        payload.get("promote"),
        payload.get("decision_reason"),
        _fmt(deltas.get("recall_gain")),
        _fmt(deltas.get("dangerous_fnr_drop")),
    )
    return payload


def summarize_promote(registry_path: Path, candidate_checkpoint: str) -> dict[str, Any] | None:
    payload = read_json(registry_path)
    if not isinstance(payload, list):
        raise PipelineError(f"Unexpected registry format in {registry_path}")

    matched = [entry for entry in payload if entry.get("checkpoint") == candidate_checkpoint]
    if not matched:
        LOGGER.info("promote summary unavailable (no registry entry for %s)", candidate_checkpoint)
        return None

    latest = sorted(matched, key=lambda item: item.get("timestamp", ""))[-1]
    metrics = latest.get("metrics", {}) if isinstance(latest.get("metrics", {}), dict) else {}
    LOGGER.info(
        "promote summary | status=%s model_tag=%s timestamp=%s mAP=%s dangerous_fnr=%s",
        latest.get("status"),
        latest.get("version") or latest.get("checkpoint"),
        latest.get("timestamp"),
        _fmt(metrics.get("mAP")),
        _fmt(metrics.get("dangerous_fnr")),
    )
    return latest


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    config_dir = Path(args.config_dir)
    train_cfg = config_dir / "train.yaml"
    retrain_cfg = config_dir / "retrain.yaml"
    eval_cfg = config_dir / "eval.yaml"

    try:
        run_step("train", [sys.executable, "scripts/train.py", "--config", str(train_cfg)])
        summarize_train(Path("outputs/metrics/train_metrics.jsonl"))

        run_step("retrain", [sys.executable, "scripts/retrain.py", "--config", str(retrain_cfg)])
        retrain_meta = summarize_retrain(Path("outputs/reports/retrain_metadata.json"))

        candidate_output_dir = Path(str(retrain_meta.get("candidate_output_dir", "")))
        candidate_checkpoint = candidate_output_dir / "checkpoints" / "best.pt"
        if args.candidate_tag:
            tagged_candidate = (
                Path("outputs/candidates") / args.candidate_tag / "checkpoints" / "best.pt"
            )
            if not tagged_candidate.exists():
                raise PipelineError(f"Requested candidate tag not found: {tagged_candidate}")
            candidate_checkpoint = tagged_candidate
            LOGGER.info("using tagged candidate checkpoint: %s", candidate_checkpoint)
        if not candidate_checkpoint.exists():
            raise PipelineError(
                f"Candidate checkpoint not found after retrain: {candidate_checkpoint}"
            )

        production_checkpoint = Path("outputs/checkpoints/best.pt")
        if not production_checkpoint.exists():
            raise PipelineError(
                f"Production checkpoint not found after train: {production_checkpoint}"
            )

        production_metrics_path = Path("outputs/reports/production_eval.json")
        run_step(
            "evaluate",
            [
                sys.executable,
                "scripts/evaluate.py",
                "--config",
                str(eval_cfg),
                "--checkpoint",
                str(candidate_checkpoint),
            ],
        )
        candidate_metrics_path = Path("outputs/reports/eval_report.json")
        summarize_evaluate(candidate_metrics_path, "candidate")

        if not production_metrics_path.exists():
            LOGGER.info(
                "production metrics not found at %s; generating now", production_metrics_path
            )
            run_step(
                "evaluate",
                [
                    sys.executable,
                    "scripts/evaluate.py",
                    "--config",
                    str(eval_cfg),
                    "--checkpoint",
                    str(production_checkpoint),
                ],
            )
            eval_report_path = Path("outputs/reports/eval_report.json")
            if eval_report_path.exists():
                production_metrics_path.parent.mkdir(parents=True, exist_ok=True)
                production_metrics_path.write_text(
                    eval_report_path.read_text(encoding="utf-8"), encoding="utf-8"
                )
            summarize_evaluate(production_metrics_path, "production")

        run_step(
            "compare",
            [
                sys.executable,
                "scripts/compare_models.py",
                "--production-metrics",
                str(production_metrics_path),
                "--candidate-metrics",
                str(candidate_metrics_path),
                "--config",
                str(eval_cfg),
                "--output",
                "outputs/reports/model_comparison.json",
                "--output-md",
                "outputs/reports/model_comparison.md",
            ],
        )
        summarize_compare(Path("outputs/reports/model_comparison.json"))

        if args.dry_run:
            LOGGER.info("dry-run enabled: skipping promote step to avoid registry writes")
            promoted_entry = None
        else:
            run_step(
                "promote",
                [
                    sys.executable,
                    "scripts/promote_model.py",
                    "--candidate-model",
                    str(candidate_checkpoint),
                    "--production-model",
                    str(production_checkpoint),
                    "--comparison-report",
                    "outputs/reports/model_comparison.json",
                    "--registry-dir",
                    "outputs/registry",
                ],
            )
            promoted_entry = summarize_promote(
                Path("outputs/registry/registry.json"), str(candidate_checkpoint)
            )

    except PipelineError as exc:
        LOGGER.error("pipeline failed: %s", exc)
        return 1

    if promoted_entry and promoted_entry.get("status") == "rejected":
        LOGGER.info("candidate rejected by promotion policy (status=rejected)")
        return 2

    if not promoted_entry:
        LOGGER.info("pipeline completed but could not determine promoted entry")
        return 0

    promoted_metrics = (
        promoted_entry.get("metrics", {}) if isinstance(promoted_entry.get("metrics"), dict) else {}
    )
    timestamp = promoted_entry.get("timestamp") or datetime.now(timezone.utc).isoformat()
    model_tag = promoted_entry.get("version") or promoted_entry.get("checkpoint")
    LOGGER.info(
        "pipeline success | promoted_model=%s timestamp=%s mAP=%s dangerous_fnr=%s",
        model_tag,
        timestamp,
        _fmt(promoted_metrics.get("mAP")),
        _fmt(promoted_metrics.get("dangerous_fnr")),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
