#!/bin/bash
# Lanza MLflow UI en puerto 5000
# Usage: bash scripts/mlflow_ui.sh
mlflow ui --backend-store-uri ./mlruns --host 0.0.0.0 --port 5000
