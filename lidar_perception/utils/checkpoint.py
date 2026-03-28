from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import torch


class _Stateful(Protocol):
    def state_dict(self) -> dict[str, Any]: ...

    def load_state_dict(self, state_dict: dict[str, Any]) -> Any: ...


def save_checkpoint(
    path: str | Path,
    model: _Stateful,
    optimizer: _Stateful,
    epoch: int,
    metrics: dict[str, float],
    config: dict[str, Any],
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
    path: str | Path,
    model: _Stateful,
    optimizer: _Stateful | None = None,
    device: torch.device | None = None,
) -> dict[str, Any]:
    checkpoint = torch.load(Path(path), map_location=device or "cpu", weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    if isinstance(checkpoint, dict):
        return checkpoint
    raise TypeError("Checkpoint payload must be a dictionary.")
