"""AgroLidar FastAPI inference server with async execution and hardened responses."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from lidar_perception.inference import InferenceEngine
from lidar_perception.logging_config import configure_logging
from lidar_perception.scoring import HazardScorer

logger = logging.getLogger(__name__)
_engine: InferenceEngine | None = None
_limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage inference engine lifecycle.

    Args:
        app: FastAPI app instance.

    Yields:
        None while the application is serving requests.
    """
    global _engine
    configure_logging()
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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agro-lidar.vercel.app"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


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
        return InferenceResponse(
            frame_id=payload.frame_id,
            detections=result.detections,
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
async def health() -> dict[str, bool | str]:
    """Liveness endpoint for deployment probes."""
    return {"status": "ok", "engine_loaded": _engine is not None}


@app.get("/readyz", include_in_schema=False)
async def readiness() -> dict[str, bool | str]:
    """Readiness endpoint for deployment probes."""
    return {"status": "ready" if _engine is not None else "loading", "ready": _engine is not None}
