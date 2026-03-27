from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export model artifact for edge deployment handoff"
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", default="outputs/exports/model.pt")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.checkpoint, out)
    print(f"exported={out}")


if __name__ == "__main__":
    main()
