from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(output_dir: str) -> logging.Logger:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("lidar_perception")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(Path(output_dir) / "run.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
