from __future__ import annotations

import base64
import binascii
import logging
import traceback
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal, cast

import numpy as np
import torch
from numpy.typing import NDArray
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from inference_server.config import InferenceServerConfig, load_server_config
from inference_server.health import uptime_seconds, utc_now
from inference_server.middleware import RequestLoggingMiddleware
from inference_server.models import (
    BEVFrameInput,
    HealthResponse,
    MetricsResponse,
    PredictionResponse,
)
from inference_server.predictor import BEVPredictor
from lidar_perception.embedding import compute_pointcloud_embedding

logger = logging.getLogger("inference_server")
TorchError = getattr(torch, "TorchError", RuntimeError)
HealthStatus = Literal["healthy", "degraded", "unhealthy"]
CollisionRisk = Literal["high", "medium", "low", "none"]


def _decode_frame(frame_data_b64: str) -> NDArray[np.float32]:
    try:
        raw = base64.b64decode(frame_data_b64)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("frame_data is not valid base64") from exc

    expected_elements = 4 * 512 * 512
    expected_bytes = expected_elements * np.dtype(np.float32).itemsize
    if len(raw) != expected_bytes:
        raise ValueError(f"Invalid payload size: {len(raw)} bytes; expected {expected_bytes}")

    return np.frombuffer(raw, dtype=np.float32).reshape((4, 512, 512))


def _dangerous_objects_count(detections: list[dict[str, Any]]) -> int:
    return sum(1 for item in detections if item["class_name"] in {"human", "animal"})


def _status_from_predictor(predictor: BEVPredictor) -> HealthStatus:
    if not predictor.model_loaded:
        return "unhealthy"
    return "healthy" if predictor.is_healthy() else "degraded"


def _get_predictor_or_503(app: FastAPI) -> BEVPredictor:
    predictor = getattr(app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not available")
    return cast(BEVPredictor, predictor)


def _record_metrics(app: FastAPI, detections_data: list[dict[str, Any]], dangerous_objects: int) -> None:
    meta = app.state.metrics
    meta["successful_requests"] += 1
    meta["last_inference_timestamp"] = utc_now().isoformat()
    meta["dangerous_detections_total"] += dangerous_objects
    class_counter = meta["detections_by_class"]
    for det in detections_data:
        class_counter[det["class_name"]] += 1


def _augment_with_vector_context(
    app: FastAPI,
    payload: BEVFrameInput,
    frame: NDArray[np.float32],
) -> list[str]:
    if app.state.vector_db is None:
        return []
    embedding = compute_pointcloud_embedding(frame.reshape(-1, frame.shape[0]))
    app.state.vector_db.add_embedding(payload.frame_id, embedding, {"timestamp": payload.timestamp})
    app.state.metrics["vector_queries"] += 1
    return cast(list[str], app.state.vector_db.query(embedding, k=5))


def _predict_one(app: FastAPI, payload: BEVFrameInput, request: Request) -> PredictionResponse:
    request.state.frame_id = payload.frame_id
    predictor = _get_predictor_or_503(app)
    app.state.metrics["total_requests"] += 1

    try:
        frame = _decode_frame(payload.frame_data)
        detections = predictor.predict(frame)
        detections_data = [item.model_dump() for item in detections]
        dangerous_objects = _dangerous_objects_count(detections_data)
        collision_risk = cast(CollisionRisk, predictor.last_collision_risk)

        _record_metrics(app, detections_data, dangerous_objects)

        if dangerous_objects > 0:
            logger.warning("Dangerous objects detected", extra={"frame_id": payload.frame_id})
        if collision_risk == "high":
            logger.critical("High collision risk", extra={"frame_id": payload.frame_id})

        similar_scene_ids = _augment_with_vector_context(app, payload, frame)
        return PredictionResponse(
            frame_id=payload.frame_id,
            timestamp=payload.timestamp,
            detections=detections,
            inference_time_ms=predictor.last_latency_ms,
            model_version=predictor.model_version,
            dangerous_objects=dangerous_objects,
            collision_risk=collision_risk,
            metadata={"similar_scene_ids": similar_scene_ids} if similar_scene_ids else None,
        )
    except Exception:
        app.state.metrics["failed_requests"] += 1
        raise


def create_app(config: InferenceServerConfig | None = None) -> FastAPI:
    runtime_config = config or load_server_config()
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{runtime_config.limits.rate_limit_per_second}/second"],
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.config = runtime_config
        app.state.started_at = utc_now()
        app.state.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "detections_by_class": Counter(),
            "dangerous_detections_total": 0,
            "last_inference_timestamp": None,
            "vector_queries": 0,
        }

        try:
            app.state.predictor = BEVPredictor(
                checkpoint_path=runtime_config.model.checkpoint_path,
                config_path=runtime_config.model.config_path,
                device=runtime_config.model.device,
                warmup_runs=runtime_config.model.warmup_runs,
                p95_latency_threshold_ms=runtime_config.health.p95_latency_threshold_ms,
                min_healthy_inferences=runtime_config.health.min_healthy_inferences,
                backend=runtime_config.model.backend,
                onnx_path=runtime_config.model.onnx_path,
            )
            logger.info("Model loaded", extra={"model_version": app.state.predictor.model_version})
        except Exception as exc:
            logger.exception("Failed to load predictor: %s", exc)
            app.state.predictor = None

        app.state.vector_db = None
        if runtime_config.vector_db.enabled:
            try:
                from lidar_perception.vector_db import VectorDBService

                app.state.vector_db = VectorDBService(
                    redis_url=runtime_config.vector_db.redis_url,
                    index_name=runtime_config.vector_db.index_name,
                )
                logger.info("Vector DB enabled")
            except Exception as exc:
                logger.exception("Failed to initialize vector DB: %s", exc)

        yield
        logger.info("Inference server graceful shutdown")

    app = FastAPI(title="AgroLidar Inference Server", version="1.0.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    async def rate_limit_handler(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    app.add_exception_handler(
        RateLimitExceeded,
        rate_limit_handler,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(RequestLoggingMiddleware)

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(TorchError)
    async def torch_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Torch error during inference: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Torch inference error"})

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled server exception: %s\n%s", exc, traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", response_model=HealthResponse)
    def health() -> JSONResponse:
        predictor = getattr(app.state, "predictor", None)
        if predictor is None:
            payload = HealthResponse(
                status="unhealthy",
                model_loaded=False,
                model_version="unknown",
                uptime_seconds=uptime_seconds(app.state.started_at),
                total_inferences=0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
            ).model_dump()
            return JSONResponse(status_code=503, content=payload)

        status = _status_from_predictor(predictor)
        payload = HealthResponse(
            status=status,
            model_loaded=predictor.model_loaded,
            model_version=predictor.model_version,
            uptime_seconds=uptime_seconds(app.state.started_at),
            total_inferences=predictor.total_inferences,
            avg_latency_ms=predictor.avg_latency_ms,
            p95_latency_ms=predictor.get_percentile_latency(95),
            p99_latency_ms=predictor.get_percentile_latency(99),
        ).model_dump()
        return JSONResponse(status_code=200 if status == "healthy" else 503, content=payload)

    @app.get("/metrics", response_model=MetricsResponse)
    def metrics() -> MetricsResponse:
        predictor = getattr(app.state, "predictor", None)
        meta = app.state.metrics
        return MetricsResponse(
            total_requests=meta["total_requests"],
            successful_requests=meta["successful_requests"],
            failed_requests=meta["failed_requests"],
            avg_inference_ms=0.0 if predictor is None else predictor.avg_latency_ms,
            p50_latency_ms=0.0 if predictor is None else predictor.get_percentile_latency(50),
            p95_latency_ms=0.0 if predictor is None else predictor.get_percentile_latency(95),
            p99_latency_ms=0.0 if predictor is None else predictor.get_percentile_latency(99),
            detections_by_class=dict(meta["detections_by_class"]),
            dangerous_detections_total=meta["dangerous_detections_total"],
            last_inference_timestamp=meta["last_inference_timestamp"],
            vector_queries=meta["vector_queries"],
        )

    @app.get("/model/info")
    def model_info() -> dict[str, Any]:
        predictor = _get_predictor_or_503(app)
        return {
            "model_version": predictor.model_version,
            "checkpoint_path": predictor.checkpoint_path,
            "classes": predictor.supported_classes,
            "input_shape": list(predictor.input_shape),
            "device": str(predictor.device),
            "backend": predictor.backend,
            "onnx_path": predictor.onnx_path if predictor.backend == "onnx" else None,
            "loaded_at": datetime.fromtimestamp(predictor.model_loaded_at, tz=timezone.utc).isoformat(),
        }

    @limiter.limit(f"{runtime_config.limits.rate_limit_per_second}/second")
    @app.post("/predict", response_model=PredictionResponse)
    def predict(request: Request, payload: BEVFrameInput) -> PredictionResponse:
        return _predict_one(app, payload, request)

    @app.post("/predict/batch", response_model=list[PredictionResponse])
    def predict_batch(request: Request, payloads: list[BEVFrameInput]) -> list[PredictionResponse]:
        if len(payloads) > app.state.config.limits.max_batch_size:
            raise ValueError(
                f"Batch size {len(payloads)} exceeds max_batch_size={app.state.config.limits.max_batch_size}"
            )
        return [_predict_one(app, payload, request) for payload in payloads]

    @app.get("/ready")
    def ready() -> JSONResponse:
        predictor = getattr(app.state, "predictor", None)
        if predictor is None or not predictor.model_loaded:
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        return JSONResponse(status_code=200, content={"status": "ready"})

    @app.get("/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    return app


app = create_app()
