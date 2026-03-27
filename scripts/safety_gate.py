from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

EXIT_PASS = 0
EXIT_BLOCK = 1
EXIT_WARN = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AgroLidar safety policy gate")
    parser.add_argument("--candidate-report", required=True, help="Path to candidate eval_report.json")
    parser.add_argument(
        "--production-report",
        default=None,
        help="Optional production eval_report.json path (regression checks skipped if missing)",
    )
    parser.add_argument("--policy", default="configs/safety_policy.yaml", help="Path to safety policy YAML")
    parser.add_argument("--output", default="outputs/reports/gate_report.json", help="Output gate_report.json path")
    parser.add_argument("--strict", action="store_true", help="Use strict policy overrides")
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _load_policy(path: Path, strict: bool) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML object at {path}")
    merged = dict(raw)
    if strict:
        strict_overrides = raw.get("strict", {})
        if not isinstance(strict_overrides, dict):
            raise ValueError("Policy 'strict' section must be a mapping")
        merged.update(strict_overrides)
    return merged


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_rule(rule: str, status: str, candidate_value: Any, threshold: Any, message: str) -> dict[str, Any]:
    return {
        "rule": rule,
        "status": status,
        "candidate_value": candidate_value,
        "threshold": threshold,
        "message": message,
    }


def evaluate_safety_gate(
    candidate_report: dict[str, Any],
    production_report: dict[str, Any] | None,
    policy: dict[str, Any],
    *,
    candidate_report_path: str,
    production_report_path: str | None,
) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    blocking_rules: list[str] = []
    warning_rules: list[str] = []

    candidate_fnr = _to_float(candidate_report.get("dangerous_fnr"), default=1.0)
    hard_limit = _to_float(policy.get("dangerous_fnr_hard_limit"), default=0.10)
    if candidate_fnr is not None and hard_limit is not None and candidate_fnr > hard_limit:
        status = "BLOCK"
        msg = f"dangerous_fnr {candidate_fnr:.6f} exceeds hard limit {hard_limit:.6f}."
        blocking_rules.append("dangerous_fnr_hard_limit")
    else:
        status = "PASS"
        msg = f"dangerous_fnr {candidate_fnr:.6f} is within hard limit {hard_limit:.6f}."
    rules.append(_build_rule("dangerous_fnr_hard_limit", status, candidate_fnr, hard_limit, msg))

    regression_tolerance = _to_float(policy.get("regression_tolerance"), default=0.02)
    prod_fnr = _to_float((production_report or {}).get("dangerous_fnr"), default=None)
    if prod_fnr is None:
        rules.append(
            _build_rule(
                "dangerous_fnr_regression",
                "PASS",
                candidate_fnr,
                None,
                "Production report unavailable; regression check skipped.",
            )
        )
    else:
        threshold = prod_fnr * (1.0 + (regression_tolerance or 0.0))
        if candidate_fnr is not None and candidate_fnr > threshold:
            status = "BLOCK"
            msg = (
                f"dangerous_fnr {candidate_fnr:.6f} regressed beyond tolerance vs production "
                f"({prod_fnr:.6f}, threshold {threshold:.6f})."
            )
            blocking_rules.append("dangerous_fnr_regression")
        else:
            status = "PASS"
            msg = (
                f"dangerous_fnr regression check passed vs production {prod_fnr:.6f} "
                f"(threshold {threshold:.6f})."
            )
        rules.append(_build_rule("dangerous_fnr_regression", status, candidate_fnr, threshold, msg))

    human_recall = _to_float(candidate_report.get("per_class", {}).get("human", {}).get("recall"), default=None)
    human_recall_minimum = _to_float(policy.get("human_recall_minimum"), default=0.90)
    if human_recall is None or human_recall < (human_recall_minimum or 0.0):
        status = "BLOCK"
        msg = f"human recall {human_recall} is below minimum {human_recall_minimum:.6f}."
        blocking_rules.append("human_recall_minimum")
    else:
        status = "PASS"
        msg = f"human recall {human_recall:.6f} meets minimum {human_recall_minimum:.6f}."
    rules.append(_build_rule("human_recall_minimum", status, human_recall, human_recall_minimum, msg))

    animal_recall = _to_float(candidate_report.get("per_class", {}).get("animal", {}).get("recall"), default=None)
    animal_recall_minimum = _to_float(policy.get("animal_recall_minimum"), default=0.85)
    if animal_recall is None or animal_recall < (animal_recall_minimum or 0.0):
        status = "BLOCK"
        msg = f"animal recall {animal_recall} is below minimum {animal_recall_minimum:.6f}."
        blocking_rules.append("animal_recall_minimum")
    else:
        status = "PASS"
        msg = f"animal recall {animal_recall:.6f} meets minimum {animal_recall_minimum:.6f}."
    rules.append(_build_rule("animal_recall_minimum", status, animal_recall, animal_recall_minimum, msg))

    candidate_latency = _to_float(candidate_report.get("latency_ms", candidate_report.get("latency")), default=None)
    prod_latency = _to_float((production_report or {}).get("latency_ms", (production_report or {}).get("latency")), default=None)
    latency_tol = _to_float(policy.get("latency_regression_tolerance"), default=0.20)
    if prod_latency is None or candidate_latency is None:
        rules.append(
            _build_rule(
                "latency_regression",
                "PASS",
                candidate_latency,
                None,
                "Missing latency in candidate/production report; latency regression check skipped.",
            )
        )
    else:
        threshold = prod_latency * (1.0 + (latency_tol or 0.0))
        if candidate_latency > threshold:
            status = "WARN"
            msg = (
                f"latency_ms {candidate_latency:.6f} regressed vs production {prod_latency:.6f} "
                f"(warn threshold {threshold:.6f})."
            )
            warning_rules.append("latency_regression")
        else:
            status = "PASS"
            msg = f"latency_ms {candidate_latency:.6f} within tolerance vs production {prod_latency:.6f}."
        rules.append(_build_rule("latency_regression", status, candidate_latency, threshold, msg))

    candidate_map = _to_float(candidate_report.get("mAP"), default=None)
    prod_map = _to_float((production_report or {}).get("mAP"), default=None)
    map_tol = _to_float(policy.get("map_regression_tolerance"), default=0.05)
    if prod_map is None or candidate_map is None:
        rules.append(
            _build_rule(
                "map_regression",
                "PASS",
                candidate_map,
                None,
                "Missing mAP in candidate/production report; mAP regression check skipped.",
            )
        )
    else:
        threshold = prod_map * (1.0 - (map_tol or 0.0))
        if candidate_map < threshold:
            status = "WARN"
            msg = (
                f"mAP {candidate_map:.6f} regressed vs production {prod_map:.6f} "
                f"(warn threshold {threshold:.6f})."
            )
            warning_rules.append("map_regression")
        else:
            status = "PASS"
            msg = f"mAP {candidate_map:.6f} within tolerated regression bound vs production {prod_map:.6f}."
        rules.append(_build_rule("map_regression", status, candidate_map, threshold, msg))

    val_samples = candidate_report.get("val_samples")
    if val_samples is None:
        val_samples = candidate_report.get("num_val_samples")
    if val_samples is None:
        val_samples = candidate_report.get("evaluation_samples")
    min_val_samples = int(policy.get("minimum_val_samples", 50))
    try:
        val_samples_int = int(val_samples) if val_samples is not None else None
    except (TypeError, ValueError):
        val_samples_int = None
    if val_samples_int is None or val_samples_int < min_val_samples:
        status = "BLOCK"
        msg = (
            f"Validation samples {val_samples_int} below minimum {min_val_samples}; "
            "insufficient statistical evidence."
        )
        blocking_rules.append("minimum_val_samples")
    else:
        status = "PASS"
        msg = f"Validation samples {val_samples_int} satisfy minimum {min_val_samples}."
    rules.append(_build_rule("minimum_val_samples", status, val_samples_int, min_val_samples, msg))

    if blocking_rules:
        decision = "BLOCK"
        summary = f"Safety gate BLOCKED candidate due to rules: {', '.join(blocking_rules)}."
    elif warning_rules:
        decision = "WARN"
        summary = (
            "Safety gate PASSED with warnings; review regressions in rules: "
            f"{', '.join(warning_rules)}."
        )
    else:
        decision = "PASS"
        summary = "Safety gate PASSED. Candidate meets all blocking safety requirements."

    return {
        "decision": decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_report": candidate_report_path,
        "production_report": production_report_path,
        "policy_version": str(policy.get("policy_version", "unknown")),
        "rules_evaluated": rules,
        "blocking_rules": blocking_rules,
        "warning_rules": warning_rules,
        "summary": summary,
    }


def _exit_code_from_decision(decision: str) -> int:
    if decision == "PASS":
        return EXIT_PASS
    if decision == "WARN":
        return EXIT_WARN
    return EXIT_BLOCK


def main() -> int:
    args = parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        candidate_path = Path(args.candidate_report)
        production_path = Path(args.production_report) if args.production_report else None
        policy_path = Path(args.policy)

        candidate_report = _load_json(candidate_path)
        production_report = _load_json(production_path) if production_path and production_path.exists() else None
        policy = _load_policy(policy_path, args.strict)

        report = evaluate_safety_gate(
            candidate_report,
            production_report,
            policy,
            candidate_report_path=str(candidate_path),
            production_report_path=str(production_path) if production_path else None,
        )

    except Exception as exc:
        report = {
            "decision": "BLOCK",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_report": args.candidate_report,
            "production_report": args.production_report,
            "policy_version": "unknown",
            "rules_evaluated": [],
            "blocking_rules": ["gate_runtime_error"],
            "warning_rules": [],
            "summary": f"Safety gate failed with runtime error: {exc}",
        }

    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"safety_gate_decision={report['decision']} report={output_path}")
    return _exit_code_from_decision(str(report.get("decision", "BLOCK")))


if __name__ == "__main__":
    raise SystemExit(main())
