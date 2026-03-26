from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskContext:
    class_name: str
    confidence: float
    distance_m: float
    forward_m: float
    lateral_m: float
    track_consistency: float
    vehicle_speed_mps: float
    time_to_collision_s: float | None = None


class HazardScorer:
    def __init__(self, class_weights: dict[str, float], corridor_width_m: float = 3.2):
        self.class_weights = class_weights
        self.corridor_width_m = corridor_width_m

    def score(self, ctx: RiskContext) -> float:
        class_weight = float(self.class_weights.get(ctx.class_name, 0.5))
        distance_factor = max(0.05, 1.0 - min(ctx.distance_m, 60.0) / 60.0)
        corridor_factor = 1.0 if abs(ctx.lateral_m) <= self.corridor_width_m / 2.0 else 0.65
        track_factor = max(0.5, min(ctx.track_consistency, 1.0))
        speed_factor = min(1.4, 1.0 + ctx.vehicle_speed_mps / 12.0)
        ttc_factor = 1.0
        if ctx.time_to_collision_s is not None:
            ttc_factor = 1.35 if ctx.time_to_collision_s < 2.0 else (1.15 if ctx.time_to_collision_s < 4.0 else 1.0)
        score = class_weight * ctx.confidence * (0.4 + 0.6 * distance_factor) * corridor_factor * track_factor * speed_factor * ttc_factor
        return float(max(0.0, min(score, 1.0)))

    @staticmethod
    def risk_level(score: float, distance_m: float) -> str:
        if score >= 0.55 and distance_m <= 10.0:
            return "emergency"
        if score >= 0.30 and distance_m <= 22.0:
            return "warning"
        return "monitor"
