from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from scripts.export_onnx import load_wrapped_model, parse_input_shape, validate_onnx_vs_pytorch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an exported ONNX model against PyTorch outputs"
    )
    parser.add_argument("--onnx-path", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--input-shape", default="1,4,512,512")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    threshold = 1e-5 if args.strict else 1e-4
    input_shape = parse_input_shape(args.input_shape)
    model = load_wrapped_model(args.config, args.checkpoint, torch.device("cpu"))

    passed, max_diff = validate_onnx_vs_pytorch(
        onnx_path=args.onnx_path,
        model=model,
        input_shape=input_shape,
        n_samples=int(args.n_samples),
        threshold=threshold,
    )
    payload = {
        "onnx_path": str(args.onnx_path),
        "checkpoint": str(args.checkpoint),
        "n_samples": int(args.n_samples),
        "strict": bool(args.strict),
        "threshold": float(threshold),
        "validation_passed": bool(passed),
        "max_output_diff": float(max_diff),
    }
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
