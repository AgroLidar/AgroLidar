from __future__ import annotations

import importlib
import json
import platform
import subprocess  # nosec B404
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_REPORT = ROOT / "outputs/reports/installation_check.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


@dataclass
class CheckResult:
    name: str
    status: str
    message: str


class InstallationChecker:
    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    def add(self, name: str, ok: bool, message: str, *, warn: bool = False) -> None:
        status = "WARN" if warn else ("PASS" if ok else "FAIL")
        self.results.append(CheckResult(name=name, status=status, message=message))

    def run(self) -> int:
        self._check_python_version()
        self._check_requirements_imports()
        self._check_configs_present()
        self._check_output_dirs()
        self._check_production_checkpoint()
        self._check_registry()
        self._check_inference_server_import()
        self._check_onnx_model()
        self._check_mlflow_tracking_uri()
        self._check_platform_profiles()
        self._check_safety_policy()
        self._check_synthetic_generation_smoke()
        self._check_health_endpoint_if_running()

        self._print_report()
        self._write_json_summary()

        failed = [r for r in self.results if r.status == "FAIL"]
        return 1 if failed else 0

    def _check_python_version(self) -> None:
        ok = sys.version_info >= (3, 11)
        msg = f"Detected Python {platform.python_version()}"
        self.add("Python >= 3.11", ok, msg)

    def _check_requirements_imports(self) -> None:
        modules = [
            "numpy",
            "yaml",
            "torch",
            "fastapi",
            "uvicorn",
            "slowapi",
            "mlflow",
            "httpx",
            "onnx",
            "onnxruntime",
        ]
        missing: list[str] = []
        for module in modules:
            try:
                importlib.import_module(module)
            except Exception as exc:
                missing.append(f"{module} ({exc.__class__.__name__}: {exc})")

        ok = len(missing) == 0
        msg = "All key packages import successfully." if ok else f"Missing imports: {missing}"
        self.add("Requirements imports", ok, msg)

    def _check_configs_present(self) -> None:
        required = [
            ROOT / "configs/base.yaml",
            ROOT / "configs/train.yaml",
            ROOT / "configs/retrain.yaml",
            ROOT / "configs/mlflow.yaml",
            ROOT / "configs/server.yaml",
            ROOT / "configs/mining.yaml",
            ROOT / "configs/safety_policy.yaml",
        ]
        missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
        self.add(
            "Config files present",
            len(missing) == 0,
            "Required config files found." if not missing else f"Missing: {missing}",
        )

    def _check_output_dirs(self) -> None:
        dirs = [
            ROOT / "outputs/checkpoints",
            ROOT / "outputs/reports",
            ROOT / "outputs/registry",
            ROOT / "outputs/onnx",
            ROOT / "outputs/candidates",
        ]
        failed: list[str] = []
        for d in dirs:
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception:
                failed.append(str(d.relative_to(ROOT)))
        self.add(
            "Output directories",
            len(failed) == 0,
            "Output directories are available." if not failed else f"Could not create: {failed}",
        )

    def _check_production_checkpoint(self) -> None:
        ckpt = ROOT / "outputs/checkpoints/best.pt"
        self.add(
            "Production checkpoint",
            True,
            f"Found {ckpt.relative_to(ROOT)}"
            if ckpt.exists()
            else "outputs/checkpoints/best.pt missing (expected before first train run)",
            warn=not ckpt.exists(),
        )

    def _check_registry(self) -> None:
        path = ROOT / "outputs/registry/registry.json"
        if not path.exists():
            self.add(
                "Model registry",
                True,
                "outputs/registry/registry.json missing (created after promotion workflows)",
                warn=True,
            )
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            ok = isinstance(payload, list)
            self.add("Model registry", ok, "Registry JSON parsed and schema looks valid.")
        except Exception as exc:
            self.add("Model registry", False, f"Failed to parse registry: {exc}")

    def _check_inference_server_import(self) -> None:
        try:
            importlib.import_module("inference_server.main")
            self.add("Inference server import", True, "inference_server.main imports successfully")
        except Exception as exc:
            self.add("Inference server import", False, f"Import failed: {exc}")

    def _check_onnx_model(self) -> None:
        path = ROOT / "outputs/onnx/model.onnx"
        self.add(
            "ONNX model",
            True,
            f"Found {path.relative_to(ROOT)}"
            if path.exists()
            else "outputs/onnx/model.onnx missing (created after export step)",
            warn=not path.exists(),
        )

    def _check_mlflow_tracking_uri(self) -> None:
        cfg_path = ROOT / "configs/mlflow.yaml"
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            tracking_uri = str(cfg.get("tracking_uri", "./mlruns"))
            uri_path = Path(tracking_uri)
            if not uri_path.is_absolute():
                uri_path = ROOT / uri_path
            uri_path.mkdir(parents=True, exist_ok=True)
            self.add("MLflow tracking URI", True, f"Tracking URI accessible: {uri_path}")
        except Exception as exc:
            self.add("MLflow tracking URI", False, f"Could not validate tracking URI: {exc}")

    def _check_platform_profiles(self) -> None:
        profile_dir = ROOT / "configs/platforms"
        profiles = sorted(profile_dir.glob("*.yaml"))
        self.add(
            "Platform profiles",
            len(profiles) >= 1,
            f"Found {len(profiles)} profiles in configs/platforms",
        )

    def _check_safety_policy(self) -> None:
        path = ROOT / "configs/safety_policy.yaml"
        self.add(
            "Safety policy config",
            path.exists(),
            "configs/safety_policy.yaml present" if path.exists() else "Missing safety policy",
        )

    def _check_synthetic_generation_smoke(self) -> None:
        cmd = [
            sys.executable,
            "scripts/generate_synthetic_data.py",
            "--output-dir",
            "outputs/tmp_install_check_data",
            "--train-samples",
            "2",
            "--val-samples",
            "1",
            "--seed",
            "123",
        ]
        try:
            proc = subprocess.run(  # nosec B603
                cmd,
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            ok = proc.returncode == 0
            message = (
                "Synthetic data smoke test passed"
                if ok
                else proc.stderr.strip() or proc.stdout.strip()
            )
            self.add("Synthetic data generation", ok, message)
        except Exception as exc:
            self.add("Synthetic data generation", False, f"Smoke test failed to execute: {exc}")

    def _check_health_endpoint_if_running(self) -> None:
        try:
            resp = httpx.get("http://127.0.0.1:8000/health", timeout=1.5)
            ok = resp.status_code in {200, 503}
            self.add("/health endpoint", ok, f"Server responded with HTTP {resp.status_code}")
        except Exception as exc:
            self.add(
                "/health endpoint",
                True,
                f"Server not running locally; skipped live health probe ({exc}).",
                warn=True,
            )

    def _print_report(self) -> None:
        print("\nAgroLidar Installation Check")
        print("=" * 36)
        for result in self.results:
            if result.status == "PASS":
                color = GREEN
                marker = "✅"
            elif result.status == "WARN":
                color = YELLOW
                marker = "⚠️"
            else:
                color = RED
                marker = "❌"
            print(f"{color}{marker} {result.name}: {result.message}{RESET}")

    def _write_json_summary(self) -> None:
        OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "results": [asdict(item) for item in self.results],
            "overall_status": "FAIL"
            if any(r.status == "FAIL" for r in self.results)
            else "PASS_WITH_WARNINGS"
            if any(r.status == "WARN" for r in self.results)
            else "PASS",
        }
        OUTPUT_REPORT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\nJSON summary written to {OUTPUT_REPORT.relative_to(ROOT)}")


def main() -> int:
    checker = InstallationChecker()
    return checker.run()


if __name__ == "__main__":
    raise SystemExit(main())
