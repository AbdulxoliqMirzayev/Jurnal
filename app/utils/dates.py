from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def today_in_timezone(timezone: str = "Asia/Tashkent") -> date:
    return datetime.now(ZoneInfo(timezone)).date()


def parse_hhmm(value: str) -> time | None:
    raw = (value or "").strip()
    for fmt in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(raw, fmt).time().replace(second=0, microsecond=0)
        except ValueError:
            continue
    return None


def parse_period_days(period: str) -> int | None:
    return {
        "today": 1,
        "week": 7,
        "1w": 7,
        "month": 30,
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "all": None,
    }.get(period)
