from __future__ import annotations

from dataclasses import dataclass


DANGEROUS = {"human", "animal", "rock", "post"}


@dataclass
class CandidateScore:
    sample_id: str
    score: float
    reasons: list[str]
    payload: dict


def entropy_from_confidences(confidences: list[float]) -> float:
    import math

    if not confidences:
        return 0.0
    eps = 1e-8
    total = sum(confidences) + eps
    probs = [max(c / total, eps) for c in confidences]
    return float(-sum(p * math.log(p) for p in probs))


def score_candidate(sample_id: str, result: dict, cfg: dict) -> CandidateScore:
    detections = result.get("detections", [])
    reasons: list[str] = []
    score = 0.0
    if not detections:
        return CandidateScore(sample_id, 0.0, ["no_detections"], result)

    confidences = [float(d["score"]) for d in detections]
    min_conf = min(confidences)
    ent = entropy_from_confidences(confidences)
    if min_conf < cfg.get("min_score_threshold", 0.2):
        reasons.append("low_confidence")
        score += cfg.get("low_confidence_weight", 1.0) * (1.0 - min_conf)

    score += cfg.get("entropy_weight", 1.0) * ent
    if any(
        d.get("label_name") in DANGEROUS and d.get("risk_level") != "monitor" for d in detections
    ):
        reasons.append("dangerous_ambiguous")
        score += cfg.get("ambiguous_dangerous_weight", 1.2)

    if any(d.get("distance_m", 0.0) > 45.0 for d in detections):
        reasons.append("edge_of_range")
        score += cfg.get("edge_range_weight", 0.5)

    rare = [d for d in detections if d.get("label_name") in {"post", "animal"}]
    if rare:
        reasons.append("rare_class_presence")
        score += cfg.get("rare_class_weight", 0.8)

    if not reasons:
        reasons.append("high_entropy")
    return CandidateScore(sample_id, float(score), reasons, result)
