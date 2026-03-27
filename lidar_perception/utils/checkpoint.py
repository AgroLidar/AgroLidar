from __future__ import annotations

from pathlib import Path

import torch


def save_checkpoint(
    path: str | Path, model, optimizer, epoch: int, metrics: dict, config: dict
) -> None:
    val_loss = float(metrics.get("val_loss", 0.0))
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_loss": val_loss,
            "metrics": metrics,
            "config": config,
        },
        Path(path),
    )


def load_checkpoint(
    path: str | Path, model, optimizer=None, device: torch.device | None = None
) -> dict:
    checkpoint = torch.load(Path(path), map_location=device or "cpu", weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint
