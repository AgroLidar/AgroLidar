from __future__ import annotations

import time

import numpy as np
import torch


def measure_latency(model: torch.nn.Module, sample: torch.Tensor, device: torch.device, warmup: int, iterations: int) -> dict[str, float]:
    model.eval()
    with torch.no_grad():
        for _ in range(warmup):
            _ = model(sample.to(device))
        if device.type == "cuda":
            torch.cuda.synchronize(device)

        start = time.perf_counter()
        for _ in range(iterations):
            _ = model(sample.to(device))
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        elapsed = time.perf_counter() - start

    mean_ms = elapsed * 1000.0 / max(iterations, 1)
    fps = 1000.0 / mean_ms if mean_ms > 0 else 0.0
    return {"latency_ms": mean_ms, "fps": fps}


def perturb_bev(bev: torch.Tensor, severity: float = 0.2) -> torch.Tensor:
    noise = torch.randn_like(bev) * severity
    sparse_mask = (torch.rand_like(bev[:, :1]) > severity).float()
    perturbed = bev + noise
    perturbed[:, :1] = perturbed[:, :1] * sparse_mask
    return perturbed.clamp(min=0.0)


def robustness_gap(clean_metric: float, degraded_metric: float) -> dict[str, float]:
    return {"robustness_gap": float(clean_metric - degraded_metric)}
