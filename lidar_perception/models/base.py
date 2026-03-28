"""Abstract base model contract for AgroLidar perception architectures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import torch
from torch import nn


class BasePerceptionModel(nn.Module, ABC):
    """Base class for all perception models used in AgroLidar."""

    @abstractmethod
    def predict(self, bev: torch.Tensor) -> dict[str, Any]:
        """Run forward inference and return task outputs.

        Args:
            bev: Input BEV tensor.

        Returns:
            Task output dictionary for downstream inference logic.
        """

    @abstractmethod
    def export_onnx(self, output_path: str | Path, sample_input: torch.Tensor) -> Path:
        """Export model to ONNX format.

        Args:
            output_path: Destination ONNX path.
            sample_input: Example tensor used to trace the graph.

        Returns:
            Path to exported ONNX model.
        """

    @abstractmethod
    def get_safety_metrics(self) -> dict[str, float]:
        """Return built-in safety metrics for this architecture."""
