# Getting Started

## Prerequisites

- Python 3.11+
- Pip
- GNU Make
- Optional: Docker for server container tests
- Optional: Node.js 20+ for landing page development

## Setup

```bash
git clone https://github.com/AgroLidar/AgroLidar.git
cd AgroLidar
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> `open3d` is constrained to Python `<3.12` in `requirements.txt` because prebuilt wheels are not consistently available on 3.12 in this project baseline.

## Verify your environment

```bash
python scripts/check_installation.py
```

## Minimal end-to-end run

```bash
make generate-data
make train
make evaluate
```

After evaluation, inspect `outputs/reports/eval_report.json` and `outputs/reports/eval_report.md`.

## Start inference server

```bash
make serve
```

Then access API docs at `http://localhost:8000/docs`.
