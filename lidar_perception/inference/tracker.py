from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class TrackState:
    track_id: int
    label: int
    label_name: str
    box: np.ndarray
    score: float
    hazard_score: float
    risk_level: str
    relative_position: dict[str, float]
    distance_m: float
    velocity_mps: dict[str, float]
    age: int = 0
    hits: int = 1
    time_since_update: int = 0


class TemporalDetectionTracker:
    def __init__(self, config: dict | None = None):
        config = config or {}
        self.enabled = bool(config.get("enabled", True))
        self.max_track_age = int(config.get("max_track_age", 4))
        self.min_confirmed_hits = int(config.get("min_confirmed_hits", 2))
        self.association_distance_m = float(config.get("association_distance_m", 3.5))
        self.smoothing_factor = float(config.get("smoothing_factor", 0.65))
        self.score_decay = float(config.get("score_decay", 0.92))
        self.frame_dt_s = float(config.get("frame_dt_s", 0.2))
        self._next_track_id = 1
        self._tracks: list[TrackState] = []

    def reset(self) -> None:
        self._next_track_id = 1
        self._tracks.clear()

    @staticmethod
    def _distance(box_a: np.ndarray, box_b: np.ndarray) -> float:
        return float(np.linalg.norm(box_a[:2] - box_b[:2]))

    def _match_track(self, detection: dict, used_track_ids: set[int]) -> TrackState | None:
        best_track = None
        best_distance = self.association_distance_m
        for track in self._tracks:
            if track.track_id in used_track_ids or track.label != detection["label"]:
                continue
            dist = self._distance(track.box, detection["box"])
            if dist <= best_distance:
                best_track = track
                best_distance = dist
        return best_track

    def _update_track(self, track: TrackState, detection: dict) -> None:
        alpha = self.smoothing_factor
        previous_center = track.box[:2].copy()
        track.box = alpha * detection["box"] + (1.0 - alpha) * track.box
        track.score = max(float(detection["score"]), track.score * self.score_decay)
        track.hazard_score = alpha * float(detection["hazard_score"]) + (1.0 - alpha) * track.hazard_score
        track.distance_m = float(np.linalg.norm(track.box[:2]))
        track.relative_position = {
            "forward_m": float(track.box[0]),
            "lateral_m": float(track.box[1]),
        }
        delta = (track.box[:2] - previous_center) / max(self.frame_dt_s, 1e-6)
        track.velocity_mps = {
            "forward_mps": float(delta[0]),
            "lateral_mps": float(delta[1]),
            "magnitude_mps": float(np.linalg.norm(delta)),
        }
        track.risk_level = detection["risk_level"]
        track.age += 1
        track.hits += 1
        track.time_since_update = 0

    def _spawn_track(self, detection: dict) -> TrackState:
        track = TrackState(
            track_id=self._next_track_id,
            label=int(detection["label"]),
            label_name=str(detection["label_name"]),
            box=detection["box"].copy(),
            score=float(detection["score"]),
            hazard_score=float(detection["hazard_score"]),
            risk_level=str(detection["risk_level"]),
            relative_position=dict(detection["relative_position"]),
            distance_m=float(detection["distance_m"]),
            velocity_mps={"forward_mps": 0.0, "lateral_mps": 0.0, "magnitude_mps": 0.0},
        )
        self._next_track_id += 1
        self._tracks.append(track)
        return track

    def update(self, detections: list[dict]) -> list[dict]:
        if not self.enabled:
            for detection in detections:
                detection["track_id"] = -1
                detection["track_status"] = "raw"
            return detections

        used_track_ids: set[int] = set()
        for track in self._tracks:
            track.time_since_update += 1
            track.age += 1
            track.score *= self.score_decay

        updated_outputs: list[dict] = []
        for detection in detections:
            matched = self._match_track(detection, used_track_ids)
            if matched is None:
                matched = self._spawn_track(detection)
                status = "tentative"
            else:
                self._update_track(matched, detection)
                used_track_ids.add(matched.track_id)
                status = "confirmed" if matched.hits >= self.min_confirmed_hits else "tentative"

            enriched = detection.copy()
            enriched["track_id"] = matched.track_id
            enriched["track_status"] = status
            enriched["box"] = matched.box.copy()
            enriched["score"] = float(matched.score)
            enriched["hazard_score"] = float(matched.hazard_score)
            enriched["distance_m"] = float(matched.distance_m)
            enriched["relative_position"] = dict(matched.relative_position)
            enriched["velocity_mps"] = dict(matched.velocity_mps)
            updated_outputs.append(enriched)

        self._tracks = [track for track in self._tracks if track.time_since_update <= self.max_track_age]
        risk_priority = {"emergency": 0, "warning": 1, "monitor": 2}
        return sorted(
            updated_outputs,
            key=lambda item: (risk_priority.get(item["risk_level"], 3), -item["hazard_score"], item["distance_m"]),
        )
