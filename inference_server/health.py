from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def uptime_seconds(started_at: datetime) -> float:
    return max((utc_now() - started_at).total_seconds(), 0.0)
