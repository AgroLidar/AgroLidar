from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BEVFrameInput(BaseModel):
    frame_data: str
    frame_id: str
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class Detection(BaseModel):
    class_name: Literal["human", "animal", "rock", "post", "vehicle"]
    confidence: float = Field(ge=0.0, le=1.0)
    bbox_bev: list[float] = Field(min_length=5, max_length=5)
    distance_m: float = Field(ge=0.0)
    risk_level: Literal["critical", "warning", "safe"]


class PredictionResponse(BaseModel):
    frame_id: str
    timestamp: str
    detections: list[Detection]
    inference_time_ms: float = Field(ge=0.0)
    model_version: str
    dangerous_objects: int = Field(ge=0)
    collision_risk: Literal["high", "medium", "low", "none"]


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    model_loaded: bool
    model_version: str
    uptime_seconds: float = Field(ge=0.0)
    total_inferences: int = Field(ge=0)
    avg_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    p99_latency_ms: float = Field(ge=0.0)


class MetricsResponse(BaseModel):
    total_requests: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    avg_inference_ms: float = Field(ge=0.0)
    p50_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    p99_latency_ms: float = Field(ge=0.0)
    detections_by_class: dict[str, int] = Field(default_factory=dict)
    dangerous_detections_total: int = Field(ge=0)
    last_inference_timestamp: str | None = None

    model_config = ConfigDict(extra="forbid")
