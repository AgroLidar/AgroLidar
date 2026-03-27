from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROFILE_DIR = Path("configs/platforms")


@dataclass(frozen=True)
class PlatformProfile:
    platform_type: str
    nominal_speed_kmh: float
    max_speed_kmh: float
    mounting_height_m: float
    forward_offset_m: float
    lateral_offset_m: float
    pitch_deg: float
    vibration_profile: str
    power_voltage_v: int
    operating_environment: str
    stop_zone_m: float
    hazard_corridor_width_m: float
    notes: str


REQUIRED_FIELDS = {
    "platform_type",
    "nominal_speed_kmh",
    "max_speed_kmh",
    "mounting_height_m",
    "forward_offset_m",
    "lateral_offset_m",
    "pitch_deg",
    "vibration_profile",
    "power_voltage_v",
    "operating_environment",
    "stop_zone_m",
    "hazard_corridor_width_m",
    "notes",
}


def _validate_payload(payload: dict, source: Path) -> None:
    missing = sorted(REQUIRED_FIELDS - payload.keys())
    if missing:
        raise ValueError(f"Missing fields in {source}: {', '.join(missing)}")


def load_platform_profile(path: str | Path) -> PlatformProfile:
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Platform profile not found: {profile_path}")

    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Invalid profile format for {profile_path}; expected mapping")

    _validate_payload(payload, profile_path)
    return PlatformProfile(
        platform_type=str(payload["platform_type"]),
        nominal_speed_kmh=float(payload["nominal_speed_kmh"]),
        max_speed_kmh=float(payload["max_speed_kmh"]),
        mounting_height_m=float(payload["mounting_height_m"]),
        forward_offset_m=float(payload["forward_offset_m"]),
        lateral_offset_m=float(payload["lateral_offset_m"]),
        pitch_deg=float(payload["pitch_deg"]),
        vibration_profile=str(payload["vibration_profile"]),
        power_voltage_v=int(payload["power_voltage_v"]),
        operating_environment=str(payload["operating_environment"]),
        stop_zone_m=float(payload["stop_zone_m"]),
        hazard_corridor_width_m=float(payload["hazard_corridor_width_m"]),
        notes=str(payload["notes"]),
    )


def list_available_profiles() -> list[str]:
    if not PROFILE_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILE_DIR.glob("*.yaml"))
