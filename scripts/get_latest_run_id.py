from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lidar_perception.tracking import MLflowTracker


def main() -> None:
    tracker = MLflowTracker("configs/mlflow.yaml")
    run_id = tracker.latest_run_id()
    if run_id:
        print(run_id)


if __name__ == "__main__":
    main()
