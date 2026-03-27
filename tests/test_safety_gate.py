from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.safety_gate import evaluate_safety_gate


def _policy() -> dict:
    return {
        "policy_version": "test-1",
        "dangerous_fnr_hard_limit": 0.10,
        "human_recall_minimum": 0.90,
        "animal_recall_minimum": 0.85,
        "minimum_val_samples": 50,
        "regression_tolerance": 0.02,
        "latency_regression_tolerance": 0.20,
        "map_regression_tolerance": 0.05,
        "strict": {
            "dangerous_fnr_hard_limit": 0.05,
            "human_recall_minimum": 0.95,
            "animal_recall_minimum": 0.92,
            "regression_tolerance": 0.01,
        },
    }


def _candidate(**overrides: float) -> dict:
    payload = {
        "mAP": 0.8,
        "dangerous_fnr": 0.08,
        "latency_ms": 100.0,
        "val_samples": 100,
        "per_class": {
            "human": {"recall": 0.95},
            "animal": {"recall": 0.90},
        },
    }
    payload.update(overrides)
    return payload


def _production(**overrides: float) -> dict:
    payload = {
        "mAP": 0.82,
        "dangerous_fnr": 0.08,
        "latency_ms": 100.0,
        "per_class": {
            "human": {"recall": 0.94},
            "animal": {"recall": 0.89},
        },
    }
    payload.update(overrides)
    return payload


def test_gate_blocks_when_fnr_exceeds_hard_limit() -> None:
    report = evaluate_safety_gate(
        _candidate(dangerous_fnr=0.11),
        _production(),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "BLOCK"
    assert "dangerous_fnr_hard_limit" in report["blocking_rules"]


def test_gate_blocks_when_human_recall_below_minimum() -> None:
    candidate = _candidate()
    candidate["per_class"]["human"]["recall"] = 0.80
    report = evaluate_safety_gate(
        candidate,
        _production(),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "BLOCK"
    assert "human_recall_minimum" in report["blocking_rules"]


def test_gate_blocks_when_fnr_regresses_vs_production() -> None:
    report = evaluate_safety_gate(
        _candidate(dangerous_fnr=0.09),
        _production(dangerous_fnr=0.05),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "BLOCK"
    assert "dangerous_fnr_regression" in report["blocking_rules"]


def test_gate_passes_when_all_rules_satisfied() -> None:
    report = evaluate_safety_gate(
        _candidate(),
        _production(),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "PASS"
    assert report["blocking_rules"] == []
    assert report["warning_rules"] == []


def test_gate_warns_when_latency_regresses() -> None:
    report = evaluate_safety_gate(
        _candidate(latency_ms=130.0),
        _production(latency_ms=100.0),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "WARN"
    assert "latency_regression" in report["warning_rules"]


def test_gate_blocks_insufficient_val_samples() -> None:
    report = evaluate_safety_gate(
        _candidate(val_samples=10),
        _production(),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "BLOCK"
    assert "minimum_val_samples" in report["blocking_rules"]


def test_gate_strict_mode_tighter_thresholds() -> None:
    policy = _policy()
    strict_policy = dict(policy)
    strict_policy.update(policy["strict"])
    report = evaluate_safety_gate(
        _candidate(dangerous_fnr=0.06),
        _production(dangerous_fnr=0.06),
        strict_policy,
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    assert report["decision"] == "BLOCK"
    assert "dangerous_fnr_hard_limit" in report["blocking_rules"]


def test_gate_report_has_required_fields() -> None:
    report = evaluate_safety_gate(
        _candidate(),
        _production(),
        _policy(),
        candidate_report_path="candidate.json",
        production_report_path="production.json",
    )
    required = {
        "decision",
        "timestamp",
        "candidate_report",
        "production_report",
        "policy_version",
        "rules_evaluated",
        "blocking_rules",
        "warning_rules",
        "summary",
    }
    assert required.issubset(report.keys())


def _run_gate_subprocess(tmp_path: Path, candidate: dict, production: dict | None = None) -> subprocess.CompletedProcess[str]:
    candidate_path = tmp_path / "candidate_eval.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    output_path = tmp_path / "gate_report.json"

    cmd = [
        sys.executable,
        "scripts/safety_gate.py",
        "--candidate-report",
        str(candidate_path),
        "--output",
        str(output_path),
    ]

    if production is not None:
        production_path = tmp_path / "production_eval.json"
        production_path.write_text(json.dumps(production), encoding="utf-8")
        cmd.extend(["--production-report", str(production_path)])

    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def test_gate_exit_code_0_on_pass(tmp_path: Path) -> None:
    result = _run_gate_subprocess(tmp_path, _candidate(), _production())
    assert result.returncode == 0


def test_gate_exit_code_1_on_block(tmp_path: Path) -> None:
    result = _run_gate_subprocess(tmp_path, _candidate(dangerous_fnr=0.2), _production())
    assert result.returncode == 1


def test_gate_exit_code_2_on_warn(tmp_path: Path) -> None:
    result = _run_gate_subprocess(tmp_path, _candidate(latency_ms=130.0), _production())
    assert result.returncode == 2
