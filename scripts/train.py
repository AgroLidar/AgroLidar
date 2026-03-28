"""CLI adapter for model training with validated configuration.

Usage:
    python scripts/train.py --config configs/train.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys

from lidar_perception.config import TrainConfig
from lidar_perception.training import TrainingPipeline

logger = logging.getLogger(__name__)


def main() -> int:
    """Run training pipeline from command line arguments.

    Returns:
        Process exit code where ``0`` indicates success.
    """
    parser = argparse.ArgumentParser(description="Train AgroLidar perception model")
    parser.add_argument("--config", required=True, help="Path to train YAML config")
    args = parser.parse_args()

    config = TrainConfig.from_yaml(args.config)
    pipeline = TrainingPipeline(config)
    result = pipeline.run()
    if not result.success:
        logger.error("Training failed")
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
