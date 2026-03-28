"""Scoring exports for hazard and collision risk classification."""

from __future__ import annotations

from lidar_perception.risk.scoring import HazardScorer as _LegacyHazardScorer


class HazardScorer(_LegacyHazardScorer):
    """Compatibility wrapper that adds scene-level risk classification helper."""

    @staticmethod
    def classify_risk(detections: list[dict]) -> str:
        """Classify frame-level risk based on detection hazard scores.

        Args:
            detections: Detection payload list that includes ``hazard_score``.

        Returns:
            Risk string in ``SAFE``, ``CAUTION``, or ``CRITICAL``.
        """
        if not detections:
            return "SAFE"
        top_score = max(float(item.get("hazard_score", 0.0)) for item in detections)
        if top_score >= 0.55:
            return "CRITICAL"
        if top_score >= 0.3:
            return "CAUTION"
        return "SAFE"


__all__ = ["HazardScorer"]
