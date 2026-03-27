from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class MLflowTracker:
    def __init__(self, config_path: str = "configs/mlflow.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.enabled = False
        self.mlflow = None
        self.client = None
        self.experiment_name = str(self.config.get("experiment_name", "default"))
        self.experiment_id: str | None = None

        try:
            import mlflow
            from mlflow.tracking import MlflowClient

            self.mlflow = mlflow
            tracking_uri = os.getenv("MLFLOW_TRACKING_URI", str(self.config.get("tracking_uri", "./mlruns")))
            self.mlflow.set_tracking_uri(tracking_uri)
            self.client = MlflowClient(tracking_uri=tracking_uri)
            self.experiment_id = self._ensure_experiment()
            self.enabled = True
        except ImportError:
            logger.warning("MLflow no está instalado. Se continúa sin tracking en MLflow.")
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning("No se pudo inicializar MLflow (%s). Se continúa sin tracking.", exc)

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            logger.warning("Config de MLflow no encontrada en %s. Usando defaults.", self.config_path)
            return {}
        with self.config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if not isinstance(payload, dict):
            logger.warning("Config de MLflow inválida en %s. Usando defaults.", self.config_path)
            return {}
        return payload

    def _ensure_experiment(self) -> str | None:
        if not self.client:
            return None
        artifact_location = self.config.get("artifact_location")
        experiment = self.client.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            exp_id = self.client.create_experiment(
                name=self.experiment_name,
                artifact_location=artifact_location,
                tags=self.config.get("tags") or None,
            )
            return exp_id
        return experiment.experiment_id

    @contextmanager
    def start_run(self, run_name: str, tags: dict[str, Any] | None = None):
        if not self.enabled or not self.mlflow:
            yield None
            return
        merged_tags = dict(self.config.get("tags", {}))
        if tags:
            merged_tags.update(tags)
        run = None
        try:
            run = self.mlflow.start_run(
                run_name=run_name,
                experiment_id=self.experiment_id,
                tags=merged_tags,
            )
        except Exception as exc:
            logger.warning("MLflow start_run failed: %s", exc)
            yield None
            return
        try:
            yield run
        except Exception:
            self.end_run("FAILED")
            raise
        finally:
            try:
                active = self.mlflow.active_run()
                if active is not None and run is not None and active.info.run_id == run.info.run_id:
                    self.end_run("FINISHED")
            except Exception as exc:
                logger.warning("MLflow active_run check failed: %s", exc)

    def log_params(self, params_dict: dict[str, Any]) -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            safe = {k: v for k, v in params_dict.items() if v is not None}
            if safe:
                self.mlflow.log_params(safe)
        except Exception as exc:
            logger.warning("MLflow log_params failed: %s", exc)

    def log_metric(self, key: str, value: float, step: int | None = None) -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            metric_value = float(value)
            if step is None:
                self.mlflow.log_metric(key, metric_value)
            else:
                self.mlflow.log_metric(key, metric_value, step=step)
        except Exception as exc:
            logger.warning("MLflow log_metric failed: %s", exc)

    def log_metrics(self, metrics_dict: dict[str, Any], step: int | None = None) -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            payload = {}
            for key, value in metrics_dict.items():
                if isinstance(value, bool):
                    payload[key] = float(value)
                elif isinstance(value, (int, float)):
                    payload[key] = float(value)
            if not payload:
                return
            if step is None:
                self.mlflow.log_metrics(payload)
            else:
                for key, value in payload.items():
                    self.mlflow.log_metric(key, value, step=step)
        except Exception as exc:
            logger.warning("MLflow log_metrics failed: %s", exc)

    def log_config(self, config_path: str | Path) -> None:
        self.log_artifact(config_path, artifact_path="configs")

    def log_checkpoint(self, path: str | Path, name: str = "checkpoint") -> None:
        self.log_artifact(path, artifact_path=name)

    def log_eval_report(self, path: str | Path) -> None:
        self.log_artifact(path, artifact_path="reports")

    def log_artifact(self, path: str | Path, artifact_path: str | None = None) -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            target = Path(path)
            if not target.exists():
                logger.warning("Artifact no encontrado, se omite: %s", target)
                return
            self.mlflow.log_artifact(str(target), artifact_path=artifact_path)
        except Exception as exc:
            logger.warning("MLflow log_artifact failed: %s", exc)

    def log_model_summary(self, model: Any) -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            summary = str(model)
            self.mlflow.log_text(summary, artifact_file="model/model_summary.txt")
        except Exception as exc:
            logger.warning("MLflow log_model_summary failed: %s", exc)

    def set_tag(self, key: str, value: Any) -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            self.mlflow.set_tag(key, str(value))
        except Exception as exc:
            logger.warning("MLflow set_tag failed: %s", exc)

    def end_run(self, status: str = "FINISHED") -> None:
        if not self.enabled or not self.mlflow:
            return
        try:
            self.mlflow.end_run(status=status)
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning("MLflow end_run failed: %s", exc)

    def latest_run_id(self, run_type: str | None = None) -> str | None:
        if not self.enabled or not self.client or not self.experiment_id:
            return None
        filter_string = ""
        if run_type:
            filter_string = f"tags.run_type = '{run_type}'"
        runs = self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string=filter_string,
            max_results=1,
            order_by=["attributes.start_time DESC"],
        )
        if not runs:
            return None
        return runs[0].info.run_id


def flatten_dict(payload: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in payload.items():
        compound = f"{parent_key}{sep}{key}" if parent_key else str(key)
        if isinstance(value, dict):
            flattened.update(flatten_dict(value, compound, sep))
        else:
            flattened[compound] = value
    return flattened
