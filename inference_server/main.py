from __future__ import annotations

import base64
import binascii
import logging
import traceback
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import numpy as np
import torch
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
from inference_server.models import BEVFrameInput, HealthResponse, MetricsResponse, PredictionResponse
from inference_server.predictor import BEVPredictor

logger = logging.getLogger("inference_server")


def _decode_frame(frame_data_b64: str) -> np.ndarray:
    try:
        raw = base64.b64decode(frame_data_b64)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("frame_data is not valid base64") from exc

    expected_elements = 4 * 512 * 512
    expected_bytes = expected_elements * np.dtype(np.float32).itemsize
    if len(raw) != expected_bytes:
        raise ValueError(f"Invalid payload size: {len(raw)} bytes; expected {expected_bytes}")

    arr = np.frombuffer(raw, dtype=np.float32)
    return arr.reshape((4, 512, 512))


def _dangerous_objects_count(detections: list[dict[str, Any]]) -> int:
    return sum(1 for item in detections if item["class_name"] in {"human", "animal"})


def _status_from_predictor(predictor: BEVPredictor) -> str:
    if not predictor.model_loaded:
        return "unhealthy"
    if predictor.is_healthy():
        return "healthy"
    return "degraded"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config: InferenceServerConfig = load_server_config()
    app.state.config = config
    app.state.started_at = utc_now()
    app.state.metrics = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "detections_by_class": Counter(),
        "dangerous_detections_total": 0,
        "last_inference_timestamp": None,
    }

    try:
        app.state.predictor = BEVPredictor(
            checkpoint_path=config.model.checkpoint_path,
            config_path=config.model.config_path,
            device=config.model.device,
            warmup_runs=config.model.warmup_runs,
            p95_latency_threshold_ms=config.health.p95_latency_threshold_ms,
            min_healthy_inferences=config.health.min_healthy_inferences,
        )
        logger.info("Model loaded", extra={"model_version": app.state.predictor.model_version})
    except Exception as exc:
        logger.exception("Failed to load predictor: %s", exc)
        app.state.predictor = None

    yield

    logger.info("Inference server graceful shutdown")


app = FastAPI(title="AgroLidar Inference Server", version="1.0.0", lifespan=lifespan)
server_config = load_server_config()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{server_config.limits.rate_limit_per_second}/second"])
app.state.limiter = limiter

app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, lambda req, exc: JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}))
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


TorchError = getattr(torch, "TorchError", RuntimeError)


@app.exception_handler(TorchError)
async def torch_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Torch error during inference: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Torch inference error"})


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled server exception: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def _get_predictor_or_503() -> BEVPredictor:
    predictor = getattr(app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not available")
    return predictor


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
    code = 200 if status == "healthy" else 503
    return JSONResponse(status_code=code, content=payload)


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
    )


@app.get("/model/info")
def model_info() -> dict[str, Any]:
    predictor = _get_predictor_or_503()
    return {
        "model_version": predictor.model_version,
        "checkpoint_path": predictor.checkpoint_path,
        "classes": ["human", "animal", "rock", "post", "vehicle"],
        "input_shape": list(BEVPredictor.EXPECTED_SHAPE),
        "device": str(predictor.device),
        "loaded_at": datetime.fromtimestamp(predictor.model_loaded_at, tz=timezone.utc).isoformat(),
    }


@limiter.limit(f"{server_config.limits.rate_limit_per_second}/second")
@app.post("/predict", response_model=PredictionResponse)
def predict(request: Request, payload: BEVFrameInput) -> PredictionResponse:
    request.state.frame_id = payload.frame_id
    predictor = _get_predictor_or_503()
    app.state.metrics["total_requests"] += 1
    try:
        frame = _decode_frame(payload.frame_data)
        detections = predictor.predict(frame)
        detections_data = [item.model_dump() for item in detections]
        dangerous_objects = _dangerous_objects_count(detections_data)
        collision_risk = predictor.last_collision_risk

        app.state.metrics["successful_requests"] += 1
        app.state.metrics["last_inference_timestamp"] = utc_now().isoformat()
        app.state.metrics["dangerous_detections_total"] += dangerous_objects
        class_counter = app.state.metrics["detections_by_class"]
        for det in detections_data:
            class_counter[det["class_name"]] += 1

        if dangerous_objects > 0:
            logger.warning("Dangerous objects detected for frame_id=%s", payload.frame_id)
        if collision_risk == "high":
            logger.critical("High collision risk on frame_id=%s detections=%s", payload.frame_id, detections_data)

        return PredictionResponse(
            frame_id=payload.frame_id,
            timestamp=payload.timestamp,
            detections=detections,
            inference_time_ms=predictor._latencies_ms[-1] if predictor._latencies_ms else 0.0,
            model_version=predictor.model_version,
            dangerous_objects=dangerous_objects,
            collision_risk=collision_risk,
        )
    except Exception:
        app.state.metrics["failed_requests"] += 1
        raise


@app.post("/predict/batch", response_model=list[PredictionResponse])
def predict_batch(request: Request, payloads: list[BEVFrameInput]) -> list[PredictionResponse]:
    predictor = _get_predictor_or_503()
    max_batch = app.state.config.limits.max_batch_size
    if len(payloads) > max_batch:
        raise ValueError(f"Batch size {len(payloads)} exceeds max_batch_size={max_batch}")

    responses: list[PredictionResponse] = []
    for payload in payloads:
        request.state.frame_id = payload.frame_id
        app.state.metrics["total_requests"] += 1
        try:
            frame = _decode_frame(payload.frame_data)
            detections = predictor.predict(frame)
            detections_data = [item.model_dump() for item in detections]
            dangerous_objects = _dangerous_objects_count(detections_data)
            collision_risk = predictor.last_collision_risk

            app.state.metrics["successful_requests"] += 1
            app.state.metrics["last_inference_timestamp"] = utc_now().isoformat()
            app.state.metrics["dangerous_detections_total"] += dangerous_objects
            class_counter = app.state.metrics["detections_by_class"]
            for det in detections_data:
                class_counter[det["class_name"]] += 1

            responses.append(
                PredictionResponse(
                    frame_id=payload.frame_id,
                    timestamp=payload.timestamp,
                    detections=detections,
                    inference_time_ms=predictor._latencies_ms[-1] if predictor._latencies_ms else 0.0,
                    model_version=predictor.model_version,
                    dangerous_objects=dangerous_objects,
                    collision_risk=collision_risk,
                )
            )
        except Exception:
            app.state.metrics["failed_requests"] += 1
            raise
    return responses


@app.get("/ready")
def ready() -> JSONResponse:
    predictor = getattr(app.state, "predictor", None)
    if predictor is None or not predictor.model_loaded:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}
