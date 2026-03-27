from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import onnx
import torch

from lidar_perception.models.factory import build_model
from lidar_perception.utils.checkpoint import load_checkpoint
from lidar_perception.utils.config import load_config


class ONNXExportWrapper(torch.nn.Module):
    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, bev_frame: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = self.model(bev_frame)
        detections = outputs["detection"]["heatmap"]
        confidence_scores = outputs["detection"]["confidence"]
        return detections, confidence_scores


def parse_input_shape(raw: str) -> tuple[int, ...]:
    values = tuple(int(chunk.strip()) for chunk in raw.split(",") if chunk.strip())
    if len(values) != 4:
        raise ValueError(f"Invalid --input-shape {raw!r}, expected 4 dimensions like 1,4,512,512")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export AgroLidar model to ONNX")
    parser.add_argument("--checkpoint", default="outputs/checkpoints/best.pt")
    parser.add_argument("--output", default="outputs/onnx/model.onnx")
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument("--input-shape", default="1,4,512,512")
    parser.add_argument("--simplify", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--config", default="configs/base.yaml")
    return parser.parse_args()


def load_wrapped_model(config_path: str, checkpoint_path: str, device: torch.device) -> ONNXExportWrapper:
    config = load_config(config_path)
    model = build_model(config["model"]).to(device)
    load_checkpoint(checkpoint_path, model=model, device=device)
    model.eval()
    return ONNXExportWrapper(model).to(device).eval()


def _to_numpy(tensor: torch.Tensor) -> np.ndarray:
    return tensor.detach().cpu().numpy().astype(np.float32)


def validate_onnx_vs_pytorch(
    onnx_path: str | Path,
    model: ONNXExportWrapper,
    input_shape: tuple[int, ...],
    n_samples: int = 10,
    threshold: float = 1e-4,
) -> tuple[bool, float]:
    import onnxruntime as ort

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    output_names = [output.name for output in session.get_outputs()]

    rows: list[dict[str, Any]] = []
    global_max = 0.0

    with torch.no_grad():
        for _ in range(n_samples):
            sample = torch.rand(input_shape, dtype=torch.float32)
            pt_outputs = model(sample)
            ort_outputs = session.run(output_names, {input_name: sample.numpy().astype(np.float32)})
            for index, name in enumerate(output_names):
                pt = _to_numpy(pt_outputs[index])
                ort_out = ort_outputs[index].astype(np.float32)
                diff = np.abs(pt - ort_out)
                max_abs = float(np.max(diff))
                mean_abs = float(np.mean(diff))
                global_max = max(global_max, max_abs)
                rows.append(
                    {
                        "output": name,
                        "max_absolute_diff": max_abs,
                        "mean_absolute_diff": mean_abs,
                    }
                )

    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        name = str(row["output"])
        current = grouped.get(name, {"max_absolute_diff": 0.0, "mean_absolute_diff": 0.0, "count": 0.0})
        current["max_absolute_diff"] = max(current["max_absolute_diff"], float(row["max_absolute_diff"]))
        current["mean_absolute_diff"] += float(row["mean_absolute_diff"])
        current["count"] += 1.0
        grouped[name] = current

    print("\nValidation diff summary (PyTorch vs ONNX):")
    print("| Output | Max Abs Diff | Mean Abs Diff |")
    print("|--------|---------------|---------------|")
    for name, stats in grouped.items():
        mean = stats["mean_absolute_diff"] / max(stats["count"], 1.0)
        print(f"| {name} | {stats['max_absolute_diff']:.6e} | {mean:.6e} |")

    return global_max < threshold, global_max


def benchmark_latency(
    model_fn: Callable[[torch.Tensor], Any],
    input_tensor: torch.Tensor,
    n_warmup: int = 10,
    n_runs: int = 100,
) -> dict[str, float]:
    for _ in range(n_warmup):
        model_fn(input_tensor)

    timings_ms: list[float] = []
    for _ in range(n_runs):
        started = time.perf_counter()
        model_fn(input_tensor)
        timings_ms.append((time.perf_counter() - started) * 1000.0)

    values = np.asarray(timings_ms, dtype=np.float64)
    return {
        "mean_ms": float(np.mean(values)),
        "std_ms": float(np.std(values)),
        "p50_ms": float(np.percentile(values, 50)),
        "p90_ms": float(np.percentile(values, 90)),
        "p95_ms": float(np.percentile(values, 95)),
        "p99_ms": float(np.percentile(values, 99)),
    }


def print_benchmark_table(torch_metrics: dict[str, float], onnx_metrics: dict[str, float]) -> None:
    print("\nLatency benchmark summary:")
    print("| Metric | PyTorch | ONNX | Speedup |")
    print("|--------|---------|------|---------|")
    for metric in ("mean_ms", "p95_ms", "p99_ms"):
        torch_value = max(torch_metrics[metric], 1e-9)
        onnx_value = max(onnx_metrics[metric], 1e-9)
        speedup = torch_value / onnx_value
        print(f"| {metric} | {torch_value:.4f} | {onnx_value:.4f} | {speedup:.2f}x |")


def main() -> None:
    args = parse_args()
    input_shape = parse_input_shape(args.input_shape)
    device = torch.device("cpu")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = load_wrapped_model(args.config, args.checkpoint, device)
    dummy_input = torch.randn(input_shape, dtype=torch.float32, device=device)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        opset_version=args.opset,
        input_names=["bev_frame"],
        output_names=["detections", "confidence_scores"],
        dynamic_axes={
            "bev_frame": {0: "batch_size"},
            "detections": {0: "batch_size"},
            "confidence_scores": {0: "batch_size"},
        },
        do_constant_folding=True,
    )
    print(f"Exported ONNX model to {output_path}")

    onnx_model = onnx.load(str(output_path))
    onnx.checker.check_model(onnx_model)
    print("ONNX model checker: PASSED")

    simplified = False
    if args.simplify:
        from onnxsim import simplify

        simplified_model, success = simplify(onnx_model)
        if not success:
            raise RuntimeError("onnx-simplifier returned unsuccessful status")
        onnx.save(simplified_model, str(output_path))
        simplified = True
        print("ONNX simplification: PASSED")

    validation_passed = False
    max_output_diff = 0.0
    if args.validate:
        validation_passed, max_output_diff = validate_onnx_vs_pytorch(output_path, model, input_shape)
        if not validation_passed:
            print(f"Validation FAILED: max_output_diff={max_output_diff:.6e}")
        else:
            print(f"Validation PASSED: max_output_diff={max_output_diff:.6e}")

    pytorch_latency = 0.0
    onnx_latency = 0.0
    speedup_ratio = 0.0
    if args.benchmark:
        import onnxruntime as ort

        ort_session = ort.InferenceSession(str(output_path), providers=["CPUExecutionProvider"])
        ort_input_name = ort_session.get_inputs()[0].name
        ort_output_names = [out.name for out in ort_session.get_outputs()]

        bench_input = torch.rand(input_shape, dtype=torch.float32)

        def pytorch_fn(x: torch.Tensor) -> Any:
            with torch.no_grad():
                return model(x)

        def onnx_fn(x: torch.Tensor) -> Any:
            return ort_session.run(ort_output_names, {ort_input_name: x.numpy().astype(np.float32)})

        pt_metrics = benchmark_latency(pytorch_fn, bench_input)
        onnx_metrics = benchmark_latency(onnx_fn, bench_input)
        print_benchmark_table(pt_metrics, onnx_metrics)

        pytorch_latency = pt_metrics["mean_ms"]
        onnx_latency = onnx_metrics["mean_ms"]
        speedup_ratio = pytorch_latency / max(onnx_latency, 1e-9)

    metadata = {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_checkpoint": str(args.checkpoint),
        "onnx_path": str(output_path),
        "opset_version": int(args.opset),
        "input_shape": list(input_shape),
        "model_size_mb": round(output_path.stat().st_size / (1024 * 1024), 6),
        "simplified": simplified,
        "validated": bool(args.validate),
        "validation_passed": bool(validation_passed) if args.validate else False,
        "max_output_diff": float(max_output_diff),
        "pytorch_latency_ms": float(pytorch_latency),
        "onnx_latency_ms": float(onnx_latency),
        "speedup_ratio": float(speedup_ratio),
    }
    metadata_path = output_path.parent / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote metadata: {metadata_path}")

    if args.validate and not validation_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
