"""AgroLidar FastAPI inference server with async execution and hardened responses."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any, cast

import numpy as np
import psutil
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from lidar_perception.inference import InferenceEngine
from lidar_perception.logging_config import configure_logging
from lidar_perception.scoring import HazardScorer

logger = logging.getLogger(__name__)
_engine: InferenceEngine | None = None
_limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage inference engine lifecycle.

    Args:
        app: FastAPI app instance.

    Yields:
        None while the application is serving requests.
    """
    global _engine
    configure_logging()
    tracer_provider = TracerProvider(resource=Resource.create({"service.name": "agrolidar-api"}))
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )
    trace.set_tracer_provider(tracer_provider)

    logger.info("Loading production model")
    _engine = InferenceEngine.load_production()
    logger.info("Inference engine ready", extra={"model_path": str(_engine.model_path)})
    yield
    logger.info("Shutting down inference engine")
    _engine = None


app = FastAPI(
    title="AgroLidar Inference API",
    version="1.0.0",
    description="Safety-critical LiDAR perception for agricultural machinery",
    lifespan=lifespan,
)
app.state.limiter = _limiter
app.add_exception_handler(
    RateLimitExceeded,
    cast(Any, _rate_limit_exceeded_handler),  # slowapi publishes a narrower signature
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agro-lidar.vercel.app"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


class PointCloudRequest(BaseModel):
    """Raw LiDAR point cloud input for a single inference frame."""

    points: list[list[float]] = Field(
        ...,
        description="List of [x, y, z, intensity] points",
        min_length=1,
        max_length=200_000,
    )
    frame_id: str = Field(..., description="Unique frame identifier for tracking")
    sensor_height_m: float = Field(default=1.5, gt=0.0, le=5.0)


class DetectedObject(BaseModel):
    """A single detected obstacle with safety metadata."""

    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    distance_m: float = Field(ge=0.0)
    hazard_score: float = Field(ge=0.0, le=1.0)
    bbox_3d: list[float] = Field(description="[x, y, z, l, w, h, yaw]")
    is_dangerous_class: bool


class InferenceResponse(BaseModel):
    """Full inference result for a single LiDAR frame."""

    frame_id: str
    detections: list[DetectedObject]
    processing_time_ms: float
    model_version: str
    collision_risk_level: str = Field(description="SAFE | CAUTION | CRITICAL")


class ErrorResponse(BaseModel):
    """API-safe error payload."""

    detail: str


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions without exposing stack traces to clients.

    Args:
        request: Current request object.
        exc: Raised exception.

    Returns:
        Sanitized JSON error response.
    """
    logger.exception("Unhandled server error", extra={"path": str(request.url.path)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.post("/v1/infer", response_model=InferenceResponse, responses={500: {"model": ErrorResponse}})
@_limiter.limit("30/minute")
async def infer(request: Request, payload: PointCloudRequest) -> InferenceResponse:
    """Run obstacle detection on a single LiDAR point cloud frame.

    Args:
        request: FastAPI request object required for rate limiter integration.
        payload: Input point cloud payload.

    Returns:
        Detection output with hazard metadata and global risk classification.

    Raises:
        HTTPException: When engine is unavailable or input is invalid.
    """
    _ = request
    if _engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference engine not ready",
        )

    try:
        points_np = np.array(payload.points, dtype=np.float32)
        result = await asyncio.to_thread(_engine.predict, points_np, payload.sensor_height_m)
        typed_detections = [
            DetectedObject(
                class_name=str(detection["class_name"]),
                confidence=float(detection["confidence"]),
                distance_m=float(detection["distance_m"]),
                hazard_score=float(detection["hazard_score"]),
                bbox_3d=[float(coord) for coord in detection["bbox_3d"]],
                is_dangerous_class=bool(detection["is_dangerous_class"]),
            )
            for detection in result.detections
        ]
        return InferenceResponse(
            frame_id=payload.frame_id,
            detections=typed_detections,
            processing_time_ms=result.latency_ms,
            model_version=_engine.model_version,
            collision_risk_level=HazardScorer.classify_risk(result.detections),
        )
    except ValueError as exc:
        logger.warning(
            "Invalid point cloud input",
            extra={"frame_id": payload.frame_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@app.get("/healthz", include_in_schema=False)
async def health() -> dict[str, bool | str | float]:
    """Liveness endpoint for deployment probes."""
    gpu_utilization = 0.0
    if hasattr(psutil, "cpu_percent"):
        gpu_utilization = float(psutil.cpu_percent(interval=None))
    return {
        "status": "ok",
        "engine_loaded": _engine is not None,
        "gpu_utilization": gpu_utilization,
    }


@app.get("/readyz", include_in_schema=False)
async def readiness() -> dict[str, bool | str]:
    """Readiness endpoint for deployment probes."""
    return {"status": "ready" if _engine is not None else "loading", "ready": _engine is not None}
